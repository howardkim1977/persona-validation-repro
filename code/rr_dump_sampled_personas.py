# -*- coding: utf-8 -*-
"""표집 페르소나의 세그먼트 속성 보존(패키지 루트에서 실행; analysis_ready.csv 와 nemotron_personas_korea.csv 필요).

code/generate.py::sample_personas 를 rq2_expand.py, rq2_region.py, sensitivity_teen_excluded.py 와 동일한 인자
(seed 42, floor 200, cap 600)로 차수별로 재실행하고, 추출 순서(_idx; 생성 산출물의 _idx 와 동일)별로
uuid, 원자료 속성(sex, age, province, education_level, occupation), 부여된 성별/연령대 셀,
map_persona 의 매핑값(연령대_라벨, 시도, 교육수준)을 outputs/sampled_personas_{2024,2025}.csv 에 기록한다.
원자료 속성은 페르소나 블록 첫 줄([기본 정보])에서 그대로 복원한다(build_persona_prompt 의 서식).
이 파일이 있으면 학력, 직업유무, 지역 축 스크립트가 4.1 GB 원자료 없이 속성을 재부착할 수 있다(README 참조).
원자료 전체를 차수마다 다시 읽으므로 수 분과 수 GB 의 메모리가 필요하다."""
import re
import pandas as pd
from generate import sample_personas

PAT = re.compile(r"^\[기본 정보\] 성별: (.*?) / 나이: (\d+)세 / 거주지: (.*?) / 직업: (.*) / 최종학력: (.*)$")

for wave in [2024, 2025]:
    ps = sample_personas("analysis_ready.csv", "nemotron_personas_korea.csv", wave)
    rows = []
    for i, p in enumerate(ps):
        m = PAT.match(p["persona_prompt"].split("\n", 1)[0])
        assert m, f"[기본 정보] 줄 서식 불일치: _idx={i}"
        sex, age, prov, occ, edu = m.groups(); seg = p["segments"]
        rows.append({"_idx": i, "uuid": p["uuid"], "sex": sex, "age": int(age), "province": prov,
                     "education_level": edu, "occupation": occ,
                     "성별": seg["성별"], "연령대": seg["연령대"], "연령대_라벨": seg["연령대_라벨"],
                     "시도": seg["시도"], "교육수준": seg["교육수준"]})
    df = pd.DataFrame(rows); out = f"outputs/sampled_personas_{wave}.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"저장: {out} ({len(df)}행)")
    print(df.groupby(["성별", "연령대"]).size().to_string())
