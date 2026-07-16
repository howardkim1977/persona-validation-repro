# -*- coding: utf-8 -*-
"""RQ2 지역축 추가(크로스워크 확정 후). 실측 지역코드→AREA, 페르소나 시도→약칭 정합."""
import pandas as pd, numpy as np
from generate import sample_personas
BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
AREA={1:"서울",2:"부산",3:"대구",4:"인천",5:"광주",6:"대전",7:"울산",8:"경기",9:"강원",
      10:"충북",11:"충남",12:"전북",13:"전남",14:"경북",15:"경남",16:"제주",17:"세종"}
FULL2SHORT={"서울특별시":"서울","부산광역시":"부산","대구광역시":"대구","인천광역시":"인천",
  "광주광역시":"광주","대전광역시":"대전","울산광역시":"울산","세종특별자치시":"세종","경기도":"경기",
  "강원특별자치도":"강원","충청북도":"충북","충청남도":"충남","전북특별자치도":"전북","전라남도":"전남",
  "경상북도":"경북","경상남도":"경남","제주특별자치도":"제주"}
a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig"); a24=a[a.YEAR==2024].copy()
a24["_지역"]=a24["지역"].map(AREA)
ps=sample_personas("analysis_ready.csv","nemotron_personas_korea.csv",2024)
idx2sido={i:FULL2SHORT.get(p["segments"]["시도"]) for i,p in enumerate(ps)}

def attach_region(raw_f,rec_f):
    raw=pd.read_csv(raw_f,encoding="utf-8-sig")
    order=raw["_idx"].tolist() if "_error" not in raw else raw.loc[raw["_error"].isna(),"_idx"].tolist()
    rec=pd.read_csv(rec_f,encoding="utf-8-sig").reset_index(drop=True)
    rec["_지역"]=[idx2sido[i] for i in order]
    return rec

rows=[]
for m,raw_f,rec_f in [("Gemini","outputs/synthetic_responses.csv","outputs/synthetic_recoded_gemini.csv"),
                      ("EXAONE","outputs/synthetic_exaone.csv","outputs/synthetic_recoded_exaone.csv")]:
    rec=attach_region(raw_f,rec_f)
    per_var=[]
    for v in BIN:
        errs=[]
        for k in set(a24["_지역"].dropna())&set(rec["_지역"].dropna()):
            s=a24[a24["_지역"]==k]; t=s[[v,"WT"]].dropna()
            act=np.average(t[v],weights=t["WT"]) if len(t) else np.nan
            sv=rec[rec["_지역"]==k][v].mean()
            if not np.isnan(act) and not np.isnan(sv): errs.append(abs(sv-act)*100)
        per_var.append(np.mean(errs))
    mae=np.mean(per_var)
    rows.append({"모델":m,"축":"지역(17시도)","셀MAE_%p":round(mae,1)})
    print(f"[{m}] 지역축 셀 MAE {mae:.1f}%p")
pd.DataFrame(rows).to_excel("outputs/_tmp_region.xlsx",index=False)
# 워크북 통합 시트에 추가
with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    pd.DataFrame(rows).to_excel(w,sheet_name="RQ2_지역축",index=False)
print("워크북 시트 추가: RQ2_지역축")
import os; os.remove("outputs/_tmp_region.xlsx")
