# -*- coding: utf-8 -*-
"""
map_persona.py
NVIDIA Nemotron-Personas-Korea 레코드를 검증 파이프라인 규약으로 매핑한다.

- 검증된 실제 스키마(26개 필드, HF Data Studio 기준)에 기반한다.
- 출력 규약은 recode.py / analysis_ready.csv 와 직접 병합·비교되도록 맞춘다.
    * 성별  : 라벨 문자열 "남성"/"여성"  (Nemotron의 남자/여자를 변환)
    * 연령대: 숫자 코드 1~8           (recode.py 의 AGE 사전과 동일 정의)
  generate.py 는 `from map_persona import map_persona` 로 사용한다.
"""

from typing import Dict, List, Optional

# 검증된 실제 컬럼명 (오타·누락 방지용 단일 출처)
PERSONA_NARRATIVE_COLS = [
    "professional_persona", "sports_persona", "arts_persona",
    "travel_persona", "culinary_persona", "family_persona", "persona",
]
ATTRIBUTE_COLS = [
    "cultural_background", "skills_and_expertise", "skills_and_expertise_list",
    "hobbies_and_interests", "hobbies_and_interests_list", "career_goals_and_ambitions",
]
DEMOGRAPHIC_COLS = [
    "sex", "age", "marital_status", "military_status", "family_type",
    "housing_type", "education_level", "bachelors_field", "occupation",
    "district", "province", "country",
]
ALL_COLS = ["uuid"] + PERSONA_NARRATIVE_COLS + ATTRIBUTE_COLS + DEMOGRAPHIC_COLS  # 26

# --- 연령대 코드: recode.py 의 AGE 사전과 반드시 동일하게 유지 ---
AGE = {1: "10세미만", 2: "10대", 3: "20대", 4: "30대",
       5: "40대", 6: "50대", 7: "60대", 8: "70대이상"}

# --- 성별: Nemotron(남자/여자) → 실측 라벨(남성/여성) ---
SEX_MAP = {"남자": "남성", "여자": "여성"}

# --- 교육수준: education_level → KISDI 교육수준 6구분 ---
# 표본 관측 5종 + 상위 2종(실데이터 확정 대상)을 모두 수용.
EDUCATION_MAP = {
    "초등학교": "초졸이하",
    "중학교": "중졸",
    "고등학교": "고졸",
    "2~3년제 전문대학": "전문대졸",
    "4년제 대학교": "대졸",
    "대학원(석사)": "대학원졸", "석사": "대학원졸",
    "대학원(박사)": "대학원졸", "박사": "대학원졸", "대학원": "대학원졸",
}

# --- 시도: province(약식) → KISDI 시도 표준명 ---
# 표본에서 직접 관측한 값만 확정 기재. 나머지는 실데이터 unique()로 보완.
PROVINCE_TO_SIDO = {
    "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시",
    "인천": "인천광역시", "광주": "광주광역시", "대전": "대전광역시",
    "울산": "울산광역시", "세종": "세종특별자치시",
    "경기": "경기도", "강원": "강원특별자치도",
    "충북": "충청북도", "충남": "충청남도",
    "전북": "전북특별자치도", "전남": "전라남도",
    "경상북": "경상북도", "경북": "경상북도",
    "경상남": "경상남도", "경남": "경상남도",
    "제주": "제주특별자치도",
}


def age_to_code(age: Optional[int]) -> Optional[int]:
    """Nemotron 정수 연령(19~99) → 연령대 코드(AGE 사전과 동일 정의)."""
    if age is None:
        return None
    age = int(age)
    if age < 10:
        return 1
    if age < 20:
        return 2          # 10대(10~19): age 하한 19가 여기 속함
    if age >= 70:
        return 8
    return (age // 10) + 1  # 20대=3, 30대=4, ... 60대=7


def build_persona_prompt(record: Dict,
                         include: Optional[List[str]] = None,
                         scenario_focus: bool = True) -> str:
    """합성 응답 생성용 1인칭 페르소나 프롬프트 블록 생성.
    유튜브 쇼츠 AI 생성 콘텐츠 수용성 시나리오에 미디어 소비 단서가 중요하므로
    기본 포함: persona(요약)+cultural_background+hobbies_and_interests+arts_persona.
    프롬프트에는 원자료의 자연어 값을 그대로 쓴다(남자/여자, 실연령 등).
    """
    if include is None:
        include = ["persona", "cultural_background",
                   "hobbies_and_interests", "arts_persona"]
        if not scenario_focus:
            include = ["persona", "cultural_background"]

    parts: List[str] = []
    parts.append(
        f"[기본 정보] 성별: {record.get('sex', '')} / 나이: {record.get('age', '')}세 / "
        f"거주지: {record.get('province', '')} / 직업: {record.get('occupation', '')} / "
        f"최종학력: {record.get('education_level', '')}"
    )
    labels = {
        "persona": "요약", "cultural_background": "성장·생활배경",
        "hobbies_and_interests": "취미·관심사", "arts_persona": "문화·미디어 성향",
        "professional_persona": "직업 성향", "career_goals_and_ambitions": "목표",
    }
    for col in include:
        val = record.get(col)
        if val:
            parts.append(f"[{labels.get(col, col)}] {val}")
    return "\n".join(parts)


def map_persona(record: Dict,
                prompt_include: Optional[List[str]] = None,
                strict: bool = False) -> Dict:
    """단일 페르소나 레코드 → 표준 매핑 결과.

    반환:
      uuid, segments(성별·연령대·연령대_라벨·시도·직업·교육수준),
      raw(검증용 원형), persona_prompt(합성 응답 생성용 텍스트).
    성별=라벨, 연령대=코드(1~8)로 recode.py 와 직접 정합한다.
    strict=True면 미확인 province/education 에 대해 ValueError 를 던진다.
    """
    age = record.get("age")
    sex_raw = record.get("sex")
    prov_raw = (record.get("province") or "").strip()
    edu_raw = (record.get("education_level") or "").strip()

    sido = PROVINCE_TO_SIDO.get(prov_raw)
    edu_std = EDUCATION_MAP.get(edu_raw)
    age_code = age_to_code(age)
    warnings = []
    if sido is None:
        warnings.append(f"province 미확인: '{prov_raw}'")
        sido = prov_raw
    if edu_std is None:
        warnings.append(f"education_level 미확인: '{edu_raw}'")
        edu_std = edu_raw

    result = {
        "uuid": record.get("uuid"),
        "segments": {
            "성별": SEX_MAP.get(sex_raw, sex_raw),     # 라벨(남성/여성)
            "연령대": age_code,                          # 코드 1~8 (recode AGE 정합)
            "연령대_라벨": AGE.get(age_code),            # 가독·층화 보조
            "시도": sido,
            "직업": (record.get("occupation") or "").strip(),  # KISDI 직업코드 정렬은 별도
            "교육수준": edu_std,
        },
        "raw": {
            "sex": sex_raw, "age": age,
            "province": prov_raw, "district": record.get("district"),
            "education_level": edu_raw, "occupation": record.get("occupation"),
            "marital_status": record.get("marital_status"),
            "household": record.get("family_type"),
        },
        "persona_prompt": build_persona_prompt(record, include=prompt_include),
    }
    if warnings:
        result["warnings"] = warnings
        if strict:
            raise ValueError("; ".join(warnings))
    return result


def map_persona_dataframe(df, **kwargs):
    """pandas DataFrame 일괄 매핑 헬퍼. 누락 컬럼을 먼저 검증."""
    missing = [c for c in ALL_COLS if c not in df.columns]
    if missing:
        raise KeyError(f"기대 컬럼 누락(스키마 변경 의심): {missing}")
    return [map_persona(dict(row), **kwargs) for _, row in df.iterrows()]
