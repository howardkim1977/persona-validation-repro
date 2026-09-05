# -*- coding: utf-8 -*-
"""OTT 게이트(유튜브·숏폼) 아래의 셀 크기 요약(패키지 루트에서 실행).
(1) 합성 패널: 모델·차수별 게이트 통과 페르소나 수(셀별 최소·중앙값·최대, 합계).
(2) 실측: 층화 30/70 분할 200회(rr_calibration_forms_extended.py 와 같은 seed·분할 함수)에서
    보정셋의 게이트 응답자(OTT 이용자)가 0명인 셀의 빈도와 최소 셀 n — 본문 IV-G 의
    "for the two OTT-gated items the smallest calibration cell held about two respondents at 1%
    and was empty in 1% of splits" 의 산출처.
시트: 심사_게이트셀_합성, 심사_게이트셀_실측분할."""
import numpy as np, pandas as pd
from rr_common import load_real, Real, NC, CELLS, AGES, CIDX, SEED, stratified_split, write_sheets
FRACS=[0.01,0.02,0.03,0.05,0.10,0.20,0.30]; REPS=200
rows=[]
for wave,lab,f in [(2024,"Gemini","outputs/synthetic_recoded_gemini.csv"),(2024,"EXAONE","outputs/synthetic_recoded_exaone.csv"),
                   (2025,"Gemini","outputs/synthetic_recoded_2025_gemini.csv"),(2025,"EXAONE","outputs/synthetic_recoded_2025_exaone.csv")]:
    d=pd.read_csv(f,encoding="utf-8-sig"); d=d[d["연령대"].isin(AGES)]
    g=d.groupby(["성별","연령대"])["숏폼_이용"].apply(lambda x:int(x.notna().sum()))
    r={"차수":wave,"모델":lab,"유효페르소나":len(d),"게이트통과합계":int(g.sum()),"셀최소":int(g.min()),"셀중앙값":int(g.median()),"셀최대":int(g.max())}
    for (s,a),v in g.items(): r[f"{s}_{a}"]=int(v)
    rows.append(r)
syn=pd.DataFrame(rows); print(syn.iloc[:,:7].to_string(index=False))
rows=[]
for wave in [2024,2025]:
    R=Real(load_real(wave)); gate=~np.isnan(R.Y["유튜브_이용"])
    for frac in FRACS:
        rng=np.random.default_rng(SEED); empt=[]; mins=[]
        for _ in range(REPS):
            cal=stratified_split(rng,R,frac); n=np.bincount(R.cell[cal&gate],minlength=NC); empt.append(int((n==0).sum())); mins.append(int(n.min()))
        rows.append({"차수":wave,"보정률":frac,"보정셋n(평균)":round(float(np.mean([stratified_split(np.random.default_rng(SEED),R,frac).sum()])),0),
                     "게이트빈셀수(평균)":round(float(np.mean(empt)),3),"게이트빈셀발생분할%":round(100*float(np.mean(np.array(empt)>0)),1),"게이트최소셀n(평균)":round(float(np.mean(mins)),1)})
real=pd.DataFrame(rows); print(real.to_string(index=False))
write_sheets({"심사_게이트셀_합성":syn,"심사_게이트셀_실측분할":real})
