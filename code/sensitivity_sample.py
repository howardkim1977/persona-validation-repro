# -*- coding: utf-8 -*-
"""표본 설계 상수(셀 cap) 민감도: 기존 합성을 여러 cap으로 하위표집 → RQ1·연령축 MAE 안정성.
셀별 하위표집은 기대 셀평균을 바꾸지 않으므로 결과가 상수에 둔감함을 실증(반복 5회 평균±sd)."""
import pandas as pd, numpy as np
BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CELL=["성별","연령대"]
a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig"); a24=a[a.YEAR==2024]
cw=a24.groupby(CELL)["WT"].sum(); share=(cw/cw.sum()).to_dict()
def wm(df,v):
    s=df[[v,"WT"]].dropna(); return np.average(s[v],weights=s["WT"]) if len(s) else np.nan
def postw(df,v):
    cm={k:s[v].mean() for k,s in df.groupby(CELL)}
    n=sum(share.get(k,0)*cm[k] for k in cm if k in share and not np.isnan(cm[k]))
    d=sum(share.get(k,0) for k in cm if k in share and not np.isnan(cm[k])); return n/d if d else np.nan
def rq1(df): return np.mean([abs(postw(df,v)-wm(a24,v)) for v in BIN])*100
def age_mae(df):
    e=[]
    for v in BIN:
        for k in set(a24["연령대"]):
            s=a24[a24["연령대"]==k][[v,"WT"]].dropna()
            if len(s):
                act=np.average(s[v],weights=s["WT"]); syn=df[df["연령대"]==k][v].mean()
                if not np.isnan(syn): e.append(abs(syn-act))
    return np.mean(e)*100
def subcap(df,cap,seed):
    rng=np.random.default_rng(seed)
    parts=[]
    for k,s in df.groupby(CELL):
        parts.append(s.sample(min(cap,len(s)),random_state=int(rng.integers(1e9))))
    return pd.concat(parts)

for m,f in [("Gemini","outputs/synthetic_recoded_gemini.csv"),("EXAONE","outputs/synthetic_recoded_exaone.csv")]:
    df=pd.read_csv(f,encoding="utf-8-sig")
    print(f"\n=== {m} (원 셀 최대≈600) — cap별 RQ1 MAE / 연령축 MAE (5회 평균±sd) ===")
    print(f"{'cap':>5}{'RQ1 MAE':>16}{'연령축 MAE':>16}")
    for cap in [150,200,300,400,600]:
        r=[];ag=[]
        for sd in range(5):
            sub=subcap(df,cap,sd); r.append(rq1(sub)); ag.append(age_mae(sub))
        print(f"{cap:>5}{np.mean(r):>10.1f}±{np.std(r):.2f}{np.mean(ag):>10.1f}±{np.std(ag):.2f}")
