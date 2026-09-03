# -*- coding: utf-8 -*-
"""R2-10: 10대 셀의 비교가능성 — 실측 19세만 대 합성 19세(합성 10대 셀은 전원 19세).
실측 10~19세 밴드 전체와 19세 부분집단의 가중 이용률을 함께 제시해 밴드 내 이질성을 보인다."""
import numpy as np, pandas as pd
from rr_common import *

a=load_real(2024,with_hid=False)
age=pd.read_csv("private/PanelData_20260701.csv",encoding="utf-8-sig",usecols=["YEAR","OPID","p__age1"])
age=age[age.YEAR==2024].drop_duplicates("OPID")[["OPID","p__age1"]].rename(columns={"p__age1":"p__age"})  # p__age1 = 만 나이(정수)
a=a.merge(age,on="OPID",how="left")
teen=a[a["연령대"]=="10대"]; t19=teen[teen["p__age"]==19]
print(f"실측 10대 n={len(teen)} (가중합 {teen.WT.sum():.0f}), 19세 n={len(t19)}; 연령 분포: {teen['p__age'].value_counts().sort_index().to_dict()}")

def wrate(df,v):
    t=df[[v,"WT"]].dropna(); return np.average(t[v],weights=t["WT"]) if len(t) else np.nan
rows=[]
for m,f in SYN_FILES.items():
    s=load_syn(f); st=s[s["연령대"]=="10대"]
    for sex in ["남성","여성","전체"]:
        rt=teen if sex=="전체" else teen[teen["성별"]==sex]; r19=t19 if sex=="전체" else t19[t19["성별"]==sex]
        ss=st if sex=="전체" else st[st["성별"]==sex]
        e_band=[]; e_19=[]
        for v in BIN:
            sv=ss[v].mean(); e_band.append(abs(sv-wrate(rt,v))*100); e_19.append(abs(sv-wrate(r19,v))*100)
            if sex=="전체":
                rows.append({"모델":m,"성별":sex,"지표":v,"합성19세%":round(sv*100,1),"실측10~19세%":round(wrate(rt,v)*100,1),
                             "실측19세%":round(wrate(r19,v)*100,1),"n_실측19세":int(r19[v].notna().sum())})
        rows.append({"모델":m,"성별":sex,"지표":"MAE(8지표)","합성19세%":np.nan,"실측10~19세%":round(np.mean(e_band),1),
                     "실측19세%":round(np.mean(e_19),1),"n_실측19세":int(len(r19))})
        print(f"[{m} {sex}] MAE vs 10~19세 밴드 {np.mean(e_band):.1f} pp | vs 19세만 {np.mean(e_19):.1f} pp (n19={len(r19)})")
write_sheets({"심사_10대_19세비교":pd.DataFrame(rows)})
