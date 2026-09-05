# -*- coding: utf-8 -*-
"""2024·2025 양쪽 정답지 기준 표를 논문 워크북에 추가."""
import pandas as pd, numpy as np
from openpyxl import load_workbook
BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CELL=["성별","연령대"]
a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig")
g=pd.read_csv("outputs/synthetic_recoded_gemini.csv",encoding="utf-8-sig")
e=pd.read_csv("outputs/synthetic_recoded_exaone.csv",encoding="utf-8-sig")
def wmean(df,v):
    s=df[[v,"WT"]].dropna(); return np.average(s[v],weights=s["WT"]) if len(s) else np.nan
def cwm(df,v):
    return {k:s[v].mean() for k,s in df.groupby(CELL)}
def postw(df,v,share):
    cm=cwm(df,v)
    num=sum(share.get(k,0)*cm[k] for k in cm if k in share and not np.isnan(cm[k]))
    den=sum(share.get(k,0) for k in cm if k in share and not np.isnan(cm[k]))
    return num/den if den else np.nan

# 정답지별 RQ1 표
dual={}
for yr in [2024,2025]:
    ay=a[a.YEAR==yr]
    # 조건부 문항(유튜브·숏폼은 OTT 이용자에게만 물음)은 그 문항 응답자만으로 셀 점유율을 계산한다.
    SH={v:(lambda t:(t/t.sum()).to_dict())(ay[ay[v].notna()].groupby(CELL)["WT"].sum()) for v in BIN}
    rows=[]
    for v in BIN:
        act=wmean(ay,v); gm=postw(g,v,SH[v]); em=postw(e,v,SH[v])
        rows.append({"변수":v,f"실측{yr}":round(act,4),
            "Gemini":round(gm,4),"Gemini_오차%p":round((gm-act)*100,1),
            "EXAONE":round(em,4),"EXAONE_오차%p":round((em-act)*100,1)})
    dual[yr]=pd.DataFrame(rows)

# 정답지 차수 효과 요약
eff=[]
for yr in [2024,2025]:
    d=dual[yr]
    eff.append({"정답지":yr,
        "Gemini_MAE%p":round(d["Gemini_오차%p"].abs().mean(),1),
        "EXAONE_MAE%p":round(d["EXAONE_오차%p"].abs().mean(),1),
        "AI_실측%":round(dual[yr].iloc[0][f"실측{yr}"]*100,1),
        "AI_Gemini편차%p":dual[yr].iloc[0]["Gemini_오차%p"],
        "AI_EXAONE편차%p":dual[yr].iloc[0]["EXAONE_오차%p"]})
effdf=pd.DataFrame(eff)

# 연도별 실측 변화(시점 드리프트 근거)
drift=[]
for v in BIN:
    v24=wmean(a[a.YEAR==2024],v); v25=wmean(a[a.YEAR==2025],v)
    drift.append({"변수":v,"실측2024":round(v24,4),"실측2025":round(v25,4),"증감%p":round((v25-v24)*100,1)})
driftdf=pd.DataFrame(drift)

path="outputs/validity_results.xlsx"
with pd.ExcelWriter(path,engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    dual[2024].to_excel(w,sheet_name="RQ1_정답지2024",index=False)
    dual[2025].to_excel(w,sheet_name="RQ1_정답지2025",index=False)
    effdf.to_excel(w,sheet_name="정답지차수_효과",index=False)
    driftdf.to_excel(w,sheet_name="실측_연도변화",index=False)
print("워크북 갱신: outputs/validity_results.xlsx")
print("추가 시트: RQ1_정답지2024, RQ1_정답지2025, 정답지차수_효과, 실측_연도변화")
print("\n[정답지 차수 효과]")
print(effdf.to_string(index=False))
