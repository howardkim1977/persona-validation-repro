# -*- coding: utf-8 -*-
"""합성 응답(raw 문항코드) → 분석용 정제 스키마 변환.

generate.py 출력(synthetic_responses.csv, 문항코드별 보기번호)을
analysis_ready.csv 와 동일한 변수 스키마로 변환하여 직접 비교 가능하게 한다.
실측 정제(build) 규칙과 동일한 역코딩을 적용한다.
"""
import pandas as pd, numpy as np

AGE = {1:"10세미만",2:"10대",3:"20대",4:"30대",5:"40대",6:"50대",7:"60대",8:"70대이상"}
GENDER = {1:"남성",2:"여성"}

M_DIMS = {
    "혁신성_기능": ["p__m01001","p__m01002","p__m01003","p__m01004"],
    "혁신성_쾌락": ["p__m01005","p__m01006","p__m01007","p__m01008"],
    "혁신성_사회": ["p__m01009","p__m01010","p__m01011","p__m01012"],
    "혁신성_인지": ["p__m01013","p__m01014","p__m01015","p__m01016"],
    "수용_성과기대": ["p__m01017","p__m01018"],
    "수용_노력기대": ["p__m01019","p__m01020"],
    "수용_사회영향": ["p__m01021","p__m01022"],
    "수용_촉진조건": ["p__m01023","p__m01024"],
}
MEDIA = {"OTT_이용":"p__d26001","유튜브_이용":"p__d26075","숏폼_이용":"p__d26092",
         "SNS_이용":"p__d11001","메신저_이용":"p__d22001","메타버스_이용":"p__d28001",
         "콘텐츠구독_이용":"p__d29001"}


def recode(df):
    """raw 합성응답 DataFrame → 정제 스키마."""
    o = pd.DataFrame(index=df.index)
    o["_model"] = df.get("_model"); o["_wave"] = df.get("_wave")
    # 세그먼트(생성 시 부여한 페르소나 속성)
    o["성별"] = df.get("성별")
    o["연령대"] = df.get("연령대").map(AGE) if df.get("연령대") is not None else None
    # 생성형 AI
    o["AI_인지"] = df.get("p__d31001")
    o["AI_이용여부"] = df.get("p__d31002").map({1:1, 2:0}) if "p__d31002" in df else np.nan
    o["AI_주이용서비스"] = df.get("p__d31003")
    o["AI_이용목적"] = df.get("p__d31005")
    o["AI_유료이용"] = df.get("p__d31007").map({1:1, 2:0}) if "p__d31007" in df else np.nan
    # 기술수용도·혁신성(2024) — 하위차원 평균
    for dim, cols in M_DIMS.items():
        present = [c for c in cols if c in df.columns]
        o[dim] = df[present].mean(axis=1) if present else np.nan
    # 미디어 이용행태(1=예/있다 → 1, else 0)
    for name, code in MEDIA.items():
        o[name] = df[code].map({1:1, 2:0}) if code in df.columns else np.nan
    return o


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", default="synthetic_responses.csv")
    ap.add_argument("--out", default="synthetic_recoded.csv")
    a = ap.parse_args()
    df = pd.read_csv(a.inp, encoding="utf-8-sig")
    df = df[~df.get("_error").notna()] if "_error" in df.columns else df  # 오류행 제외
    recode(df).to_csv(a.out, index=False, encoding="utf-8-sig")
    print("저장:", a.out)
