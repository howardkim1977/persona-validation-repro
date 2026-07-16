# -*- coding: utf-8 -*-
"""논문용 결과표 통합 워크북 생성: outputs/validity_results.xlsx"""
import pandas as pd, numpy as np
BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CELL=["성별","연령대"]
a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig"); a=a[a.YEAR==2024].copy()
g=pd.read_csv("outputs/synthetic_recoded_gemini.csv",encoding="utf-8-sig")
e=pd.read_csv("outputs/synthetic_recoded_exaone.csv",encoding="utf-8-sig")
def cw(df,v,w):
    o={}
    for k,s in df.groupby(CELL):
        if w: t=s[[v,"WT"]].dropna(); o[k]=np.average(t[v],weights=t["WT"]) if len(t) else np.nan
        else: o[k]=s[v].mean()
    return o
# RQ2 변수별 MAE/RMSE
r2=[]
for name,df in [("Gemini",g),("EXAONE",e)]:
    for v in BIN:
        act=cw(a,v,True); syn=cw(df,v,False)
        d=[abs(syn[k]-act[k]) for k in syn if k in act and not np.isnan(syn[k]) and not np.isnan(act[k])]
        r2.append({"모델":name,"변수":v,"셀MAE_%p":round(np.mean(d)*100,1),
                   "셀RMSE_%p":round(np.sqrt(np.mean(np.square(d)))*100,1)})
rq2sum=pd.DataFrame(r2)

rq1=pd.read_csv("outputs/validity_RQ1_overall.csv",encoding="utf-8-sig")
rq2cells=pd.read_csv("outputs/validity_RQ2_cells.csv",encoding="utf-8-sig")
constructs=pd.read_csv("outputs/validity_constructs.csv",encoding="utf-8-sig")

summary=pd.DataFrame([
    {"지표":"RQ1 전체 일치도 MAE(%p)","Gemini":17.1,"EXAONE":15.0},
    {"지표":"RQ2 세그먼트 셀 MAE(%p)","Gemini":18.9,"EXAONE":15.9},
    {"지표":"RQ2 세그먼트 셀 RMSE(%p)","Gemini":23.9,"EXAONE":18.4},
    {"지표":"구성개념 평균 MAE(5점)","Gemini":0.373,"EXAONE":0.380},
])
meta=pd.DataFrame([
    {"항목":"정답지","내용":"한국미디어패널조사(KISDI) 2024, 개인가중치 WT 적용 가중추정"},
    {"항목":"합성 표본","내용":"성별×연령대 floor+cap, 셀별 clip(실측×2,200,600), 각 모델 약 8,168"},
    {"항목":"주 모델","내용":"gemini-3.5-flash (Batch), temp 1.0, top_p 1.0, thinking=low"},
    {"항목":"비교 모델","내용":"LGAI-EXAONE/K-EXAONE-236B-A23B (FriendliAI), thinking off"},
    {"항목":"RQ1","내용":"전체 일치도 — 사후가중 합성 vs 가중 실측, 절대오차 평균"},
    {"항목":"RQ2","내용":"세그먼트 오차 — 성별×연령대 셀별 |합성−실측가중|"},
])
with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl") as w:
    meta.to_excel(w,sheet_name="개요",index=False)
    summary.to_excel(w,sheet_name="요약",index=False)
    rq1.to_excel(w,sheet_name="RQ1_전체일치도",index=False)
    rq2sum.to_excel(w,sheet_name="RQ2_변수별요약",index=False)
    rq2cells.to_excel(w,sheet_name="RQ2_셀별상세",index=False)
    constructs.to_excel(w,sheet_name="구성개념",index=False)
print("저장: outputs/validity_results.xlsx")
print("시트: 개요, 요약, RQ1_전체일치도, RQ2_변수별요약, RQ2_셀별상세, 구성개념")
