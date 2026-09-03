# -*- coding: utf-8 -*-
"""RQ2 확장: 교육·직업유무 축 세그먼트 오차 + 집단 간 부호오차 범위 R_e(논문 III-E; 구 명칭 DPD 상응 지표).
지역축은 rq2_region.py(RQ2_지역축)에서 별도 산출한다."""
import pandas as pd, numpy as np
from generate import sample_personas
BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
EDU_MAP={"초졸이하":"초졸이하","중졸":"중졸이하","고졸":"고졸이하","전문대졸":"대졸이하",
         "대졸":"대졸이하","대학원졸":"대학원이상"}
def emp(occ):
    o=str(occ)
    return "무직" if any(k in o for k in ["무직","주부","학생","군인","없음","실업"]) else "유직"

a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig"); a24=a[a.YEAR==2024]
ps=sample_personas("analysis_ready.csv","nemotron_personas_korea.csv",2024)  # seed 고정 재현
idx2seg={i:{"학력":EDU_MAP.get(p["segments"]["교육수준"]),"직업유무":emp(p["segments"]["직업"])}
         for i,p in enumerate(ps)}

def attach(raw_f,rec_f):
    raw=pd.read_csv(raw_f,encoding="utf-8-sig")
    order=raw["_idx"].tolist() if "_error" not in raw else raw.loc[raw["_error"].isna(),"_idx"].tolist()
    rec=pd.read_csv(rec_f,encoding="utf-8-sig").reset_index(drop=True)
    assert len(order)==len(rec), f"정렬 불일치 {len(order)} vs {len(rec)}"
    rec["학력"]=[idx2seg[i]["학력"] for i in order]
    rec["직업유무"]=[idx2seg[i]["직업유무"] for i in order]
    return rec

def rq2_axis(a_df,syn,axis):
    """축별 셀 MAE(%p) 및 셀별 오차 반환. 실측 가중, 합성 단순평균."""
    out={}
    for v in BIN:
        errs={}
        for k in set(a_df[axis].dropna())&set(syn[axis].dropna()):
            s=a_df[a_df[axis]==k]; t=s[[v,"WT"]].dropna()
            act=np.average(t[v],weights=t["WT"]) if len(t) else np.nan
            sv=syn[syn[axis]==k][v].mean()
            if not np.isnan(act) and not np.isnan(sv): errs[k]=(sv-act)*100
        out[v]=errs
    return out

axis_rows=[]
for m,raw_f,rec_f in [("Gemini","outputs/synthetic_responses.csv","outputs/synthetic_recoded_gemini.csv"),
                      ("EXAONE","outputs/synthetic_exaone.csv","outputs/synthetic_recoded_exaone.csv")]:
    rec=attach(raw_f,rec_f)
    print(f"\n===== {m} =====")
    for axis in ["연령대","성별","학력","직업유무"]:
        res=rq2_axis(a24,rec,axis)
        allmae=np.mean([np.mean([abs(x) for x in errs.values()]) for errs in res.values() if errs])
        print(f"  [{axis}] 셀 MAE {allmae:.1f}%p")
        axis_rows.append({"모델":m,"축":axis,"셀MAE%p":round(allmae,1),
                          "비고":"Table 5 (region axis: RQ2_지역축 from rq2_region.py)"})
    # 집단 간 부호오차 범위 R_e: 성별×연령대 셀 오차의 최대격차·SD·최악셀
    rec["_cell"]=rec["성별"].astype(str)+"·"+rec["연령대"].astype(str)
    a24c=a24.copy(); a24c["_cell"]=a24c["성별"].astype(str)+"·"+a24c["연령대"].astype(str)
    worst=[]
    for v in BIN:
        errs=[]
        for k in set(a24c["_cell"])&set(rec["_cell"]):
            s=a24c[a24c["_cell"]==k]; t=s[[v,"WT"]].dropna()
            act=np.average(t[v],weights=t["WT"]) if len(t) else np.nan
            sv=rec[rec["_cell"]==k][v].mean()
            if not np.isnan(act) and not np.isnan(sv): errs.append((k,(sv-act)*100))
        vals=[e for _,e in errs]
        rng=max(vals)-min(vals); sd=np.std(vals)
        wk,wv=max(errs,key=lambda x:abs(x[1]))
        worst.append({"모델":m,"변수":v,"Re_최대격차%p":round(rng,1),"오차SD%p":round(sd,1),
                      "최악셀":wk,"최악오차%p":round(wv,1)})
    dpd=pd.DataFrame(worst)
    print("  [R_e] 평균 최대격차 %.1f%%p"%dpd["Re_최대격차%p"].mean())
    with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
        dpd.to_excel(w,sheet_name=f"RQ2_집단편향_{m}",index=False)
with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    pd.DataFrame(axis_rows).to_excel(w,sheet_name="RQ2_축별MAE",index=False)
print("\n워크북 시트 추가: RQ2_집단편향_Gemini, RQ2_집단편향_EXAONE, RQ2_축별MAE")
