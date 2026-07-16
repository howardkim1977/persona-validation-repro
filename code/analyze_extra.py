# -*- coding: utf-8 -*-
"""RQ2 셀별 표 저장 + 구성개념(혁신성·수용도) 평균 비교."""
import pandas as pd, numpy as np
BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CONSTRUCTS=["혁신성_기능","혁신성_쾌락","혁신성_사회","혁신성_인지",
            "수용_성과기대","수용_노력기대","수용_사회영향","수용_촉진조건"]
CELL=["성별","연령대"]
a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig"); a=a[a.YEAR==2024].copy()
g=pd.read_csv("outputs/synthetic_recoded_gemini.csv",encoding="utf-8-sig")
e=pd.read_csv("outputs/synthetic_recoded_exaone.csv",encoding="utf-8-sig")

def cell_wmean(df,var,weighted):
    out={}
    for key,sub in df.groupby(CELL):
        if weighted:
            s=sub[[var,"WT"]].dropna()
            out[key]=np.average(s[var],weights=s["WT"]) if len(s) else np.nan
        else:
            out[key]=sub[var].mean()
    return out

# ── RQ2 셀별 표 ──
rows=[]
for v in BIN:
    act=cell_wmean(a,v,True); gm=cell_wmean(g,v,False); em=cell_wmean(e,v,False)
    for k in sorted(set(act)|set(gm)|set(em)):
        rows.append({"변수":v,"성별":k[0],"연령대":k[1],
            "실측_가중":round(act.get(k,np.nan),4),
            "Gemini":round(gm.get(k,np.nan),4),
            "EXAONE":round(em.get(k,np.nan),4),
            "Gemini_오차%p":round((gm.get(k,np.nan)-act.get(k,np.nan))*100,1) if k in act and k in gm else np.nan,
            "EXAONE_오차%p":round((em.get(k,np.nan)-act.get(k,np.nan))*100,1) if k in act and k in em else np.nan})
pd.DataFrame(rows).to_csv("outputs/validity_RQ2_cells.csv",index=False,encoding="utf-8-sig")
print("저장: outputs/validity_RQ2_cells.csv  (", len(rows), "행)")

# ── 구성개념 평균 비교(가중 실측 vs 사후가중 합성) ──
def wmean(df,var):
    s=df[[var,"WT"]].dropna(); return np.average(s[var],weights=s["WT"]) if len(s) else np.nan
cell_w=a.groupby(CELL)["WT"].sum(); cell_share=(cell_w/cell_w.sum()).to_dict()
def postw(df,var):
    cm=cell_wmean(df,var,False)
    num=sum(cell_share.get(k,0)*cm[k] for k in cm if k in cell_share and not np.isnan(cm[k]))
    den=sum(cell_share.get(k,0) for k in cm if k in cell_share and not np.isnan(cm[k]))
    return num/den if den else np.nan
crows=[]
print("\n구성개념 평균(5점) 비교:")
print(f"{'구성개념':<14}{'실측가중':>8}{'Gemini':>8}{'ΔG':>7}{'EXAONE':>8}{'ΔE':>7}")
for c in CONSTRUCTS:
    if c not in a.columns: continue
    act=wmean(a,c); gm=postw(g,c); em=postw(e,c)
    print(f"{c:<14}{act:>8.2f}{gm:>8.2f}{gm-act:>+7.2f}{em:>8.2f}{em-act:>+7.2f}")
    crows.append({"구성개념":c,"실측_가중":round(act,3),
        "Gemini":round(gm,3),"Gemini_오차":round(gm-act,3),
        "EXAONE":round(em,3),"EXAONE_오차":round(em-act,3)})
cdf=pd.DataFrame(crows); cdf.to_csv("outputs/validity_constructs.csv",index=False,encoding="utf-8-sig")
print("\n구성개념 MAE: Gemini",round(cdf['Gemini_오차'].abs().mean(),3),"| EXAONE",round(cdf['EXAONE_오차'].abs().mean(),3))
print("저장: outputs/validity_constructs.csv")
