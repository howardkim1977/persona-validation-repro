# -*- coding: utf-8 -*-
"""숏폼 진단 저장 + 전 지표 프레이밍/스테레오타입(연령경사) 확장 진단.
2025 문항셋 합성 vs 2025 실측(가중) 기준."""
import pandas as pd, numpy as np
BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
AGES=["10대","20대","30대","40대","50대","60대","70대이상"]
ACODE={a:i for i,a in enumerate(AGES)}
a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig"); a25=a[a.YEAR==2025]
g=pd.read_csv("outputs/synthetic_recoded_2025_gemini.csv",encoding="utf-8-sig")
e=pd.read_csv("outputs/synthetic_recoded_2025_exaone.csv",encoding="utf-8-sig")
def wrate_age(df,v):
    o={}
    for k,s in df.groupby("연령대"):
        if "WT" in df:
            t=s[[v,"WT"]].dropna(); o[k]=np.average(t[v],weights=t["WT"]) if len(t) else np.nan
        else: o[k]=s[v].mean()
    return o

# (A) 숏폼 연령 그래디언트 시트
sf_rows=[]
ar=wrate_age(a25,"숏폼_이용"); gr=wrate_age(g,"숏폼_이용"); er=wrate_age(e,"숏폼_이용")
for age in AGES:
    sf_rows.append({"연령대":age,"실측2025":round(ar.get(age,np.nan),3),
        "Gemini":round(gr.get(age,np.nan),3),"EXAONE":round(er.get(age,np.nan),3)})
sf_df=pd.DataFrame(sf_rows)

# (B) 유튜브-숏폼 일관성 시트
def cond(df,par,ch,weighted):
    sub=df[df[par]==1]
    if weighted and "WT" in df:
        t=sub[[ch,"WT"]].dropna(); return np.average(t[ch],weights=t["WT"]) if len(t) else np.nan
    return sub[ch].mean()
a24=a[a.YEAR==2024]
g24=pd.read_csv("outputs/synthetic_recoded_gemini.csv",encoding="utf-8-sig")
e24=pd.read_csv("outputs/synthetic_recoded_exaone.csv",encoding="utf-8-sig")
def marg(df,v):
    if "WT" in df: t=df[[v,"WT"]].dropna(); return np.average(t[v],weights=t["WT"]) if len(t) else np.nan
    return df[v].mean()
# 프레이밍 효과가 문항 수 교란과 무관함을 보이는 통제 증거: 문항 수 일치 2024(36문항) vs 2025(12문항)
cons_df=pd.DataFrame([
  {"차수":"2024(36문항)","지표":"숏폼 이용률","실측":round(marg(a24,"숏폼_이용"),3),
   "Gemini":round(marg(g24,"숏폼_이용"),3),"EXAONE":round(marg(e24,"숏폼_이용"),3)},
  {"차수":"2024(36문항)","지표":"P(숏폼|유튜브)","실측":round(cond(a24,"유튜브_이용","숏폼_이용",True),3),
   "Gemini":round(cond(g24,"유튜브_이용","숏폼_이용",False),3),"EXAONE":round(cond(e24,"유튜브_이용","숏폼_이용",False),3)},
  {"차수":"2025(12문항)","지표":"숏폼 이용률","실측":round(marg(a25,"숏폼_이용"),3),
   "Gemini":round(marg(g,"숏폼_이용"),3),"EXAONE":round(marg(e,"숏폼_이용"),3)},
  {"차수":"2025(12문항)","지표":"P(숏폼|유튜브)","실측":round(cond(a25,"유튜브_이용","숏폼_이용",True),3),
   "Gemini":round(cond(g,"유튜브_이용","숏폼_이용",False),3),"EXAONE":round(cond(e,"유튜브_이용","숏폼_이용",False),3)},
])

# (C) 전 지표 연령경사 오차(스테레오타입 신호)
# 각 변수: 오차(합성-실측)를 연령코드에 선형회귀 → 기울기. |기울기| 크면 연령 스테레오타입.
rows=[]
for v in BIN:
    av=wrate_age(a25,v)
    for name,df in [("Gemini",g),("EXAONE",e)]:
        sv=wrate_age(df,v)
        xs=[ACODE[k] for k in AGES if k in av and k in sv and not np.isnan(av[k]) and not np.isnan(sv[k])]
        errs=[(sv[k]-av[k])*100 for k in AGES if k in av and k in sv and not np.isnan(av[k]) and not np.isnan(sv[k])]
        if len(xs)>=3:
            slope=np.polyfit(xs,errs,1)[0]  # %p per 연령단계
            young=errs[0]; old=errs[-1]
        else: slope=young=old=np.nan
        rows.append({"변수":v,"모델":name,
            "청년오차%p(10대)":round(young,1),"고령오차%p(70대+)":round(old,1),
            "연령경사%p/단계":round(slope,1),"전체MAE기여":round(np.mean(np.abs(errs)),1)})
slope_df=pd.DataFrame(rows).sort_values("연령경사%p/단계",key=lambda s:s.abs(),ascending=False)

with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    sf_df.to_excel(w,sheet_name="진단_숏폼연령",index=False)
    cons_df.to_excel(w,sheet_name="진단_유튜브숏폼일관성",index=False)
    slope_df.to_excel(w,sheet_name="진단_연령경사오차",index=False)
print("워크북 시트 추가: 진단_숏폼연령, 진단_유튜브숏폼일관성, 진단_연령경사오차\n")
print("=== 연령경사 오차(스테레오타입 신호) — |경사| 큰 순 ===")
print(slope_df.to_string(index=False))
