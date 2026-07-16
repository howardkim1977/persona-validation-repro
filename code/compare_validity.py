# -*- coding: utf-8 -*-
"""합성 패널(Gemini·EXAONE) vs 실측 KISDI 2024 타당성 비교.
RQ1: 전체 일치도(사후가중된 합성 vs 가중 실측).
RQ2: 세그먼트(성별×연령대) 오차(셀별 대조 → MAE/RMSE).
실측은 개인가중치 WT 적용. 합성은 floor+cap 표본이므로 실측 셀분포로 재가중.
"""
import pandas as pd, numpy as np

BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용",
     "메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CELL=["성별","연령대"]

a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig")
a=a[a.YEAR==2024].copy()
g=pd.read_csv("outputs/synthetic_recoded_gemini.csv",encoding="utf-8-sig")
e=pd.read_csv("outputs/synthetic_recoded_exaone.csv",encoding="utf-8-sig")

def wmean(df,var,w="WT"):
    s=df[[var,w]].dropna()
    return np.average(s[var],weights=s[w]) if len(s) else np.nan

def cell_wmean(df,var,weighted):
    """셀별 평균. weighted=True면 WT 가중(실측), 아니면 단순평균(합성)."""
    out={}
    for key,sub in df.groupby(CELL):
        if weighted:
            s=sub[[var,"WT"]].dropna()
            out[key]=np.average(s[var],weights=s["WT"]) if len(s) else np.nan
        else:
            out[key]=sub[var].mean()
    return out

# 실측 셀분포(가중 셀 점유율) — 사후가중용
cell_w=a.groupby(CELL)["WT"].sum()
cell_share=(cell_w/cell_w.sum()).to_dict()

print("="*72)
print("RQ1  전체 일치도 (사후가중 합성 vs 가중 실측)")
print("="*72)
print(f"{'변수':<14}{'실측(가중)':>10}{'Gemini':>10}{'ΔG':>8}{'EXAONE':>10}{'ΔE':>8}")
rq1=[]
for v in BIN:
    act=wmean(a,v)
    def postw(df):
        cm=cell_wmean(df,v,False)
        num=sum(cell_share.get(k,0)*cm[k] for k in cm if k in cell_share and not np.isnan(cm[k]))
        den=sum(cell_share.get(k,0) for k in cm if k in cell_share and not np.isnan(cm[k]))
        return num/den if den else np.nan
    gm,em=postw(g),postw(e)
    print(f"{v:<14}{act*100:>9.1f}%{gm*100:>9.1f}%{(gm-act)*100:>+7.1f}{em*100:>9.1f}%{(em-act)*100:>+7.1f}")
    rq1.append((v,act,gm,em))

print("\n전체 편향 요약(절대오차 평균, %p):")
for name,idx in [("Gemini",2),("EXAONE",3)]:
    mae=np.mean([abs(r[idx]-r[1]) for r in rq1])*100
    print(f"  {name}: MAE={mae:.1f}%p")

print("\n"+"="*72)
print("RQ2  세그먼트 오차 (셀별 |합성-실측가중|, %p)")
print("="*72)
for name,df in [("Gemini",g),("EXAONE",e)]:
    per_var=[]
    for v in BIN:
        act=cell_wmean(a,v,True); syn=cell_wmean(df,v,False)
        diffs=[abs(syn[k]-act[k]) for k in syn if k in act and not np.isnan(syn[k]) and not np.isnan(act[k])]
        per_var.append((v,np.mean(diffs)*100,np.sqrt(np.mean(np.square(diffs)))*100))
    mae=np.mean([p[1] for p in per_var]); rmse=np.mean([p[2] for p in per_var])
    print(f"\n[{name}]  셀 MAE={mae:.1f}%p  RMSE={rmse:.1f}%p")
    for v,m,r in per_var:
        print(f"    {v:<14} MAE {m:>5.1f}  RMSE {r:>5.1f}")

# 결과 CSV 저장
import csv
rows=[]
for v in BIN:
    act=wmean(a,v)
    def postw(df,v=v):
        cm=cell_wmean(df,v,False)
        num=sum(cell_share.get(k,0)*cm[k] for k in cm if k in cell_share and not np.isnan(cm[k]))
        den=sum(cell_share.get(k,0) for k in cm if k in cell_share and not np.isnan(cm[k]))
        return num/den if den else np.nan
    gm,em=postw(g),postw(e)
    rows.append({"변수":v,"실측_가중":round(act,4),
                 "Gemini":round(gm,4),"Gemini_오차%p":round((gm-act)*100,1),
                 "EXAONE":round(em,4),"EXAONE_오차%p":round((em-act)*100,1)})
pd.DataFrame(rows).to_csv("outputs/validity_RQ1_overall.csv",index=False,encoding="utf-8-sig")
print("\n저장: outputs/validity_RQ1_overall.csv")
