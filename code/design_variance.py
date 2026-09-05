# -*- coding: utf-8 -*-
"""설계기반 분산: Kish 설계효과 + 가구 군집 가중 부트스트랩으로 RQ1 MAE CI 재산출.
실측은 가구(hid) 단위 복원추출(군집·가중 반영), 합성은 독립 생성이므로 행 단위 재표집."""
import pandas as pd, numpy as np
BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CELL=["성별","연령대"]
rng=np.random.default_rng(42)

a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig")
hid=pd.read_csv("private/PanelData_20260701.csv",encoding="utf-8-sig",usecols=["OPID","hid"]).drop_duplicates("OPID")
a24=a[a.YEAR==2024].merge(hid,on="OPID",how="left")
print(f"hid 결합: {a24['hid'].notna().mean()*100:.1f}% 매칭, 가구 수 {a24['hid'].nunique()}")

# ── Kish 설계효과(가중 불균등) ──
w=a24["WT"].values; n=len(w)
deff_w=n*np.sum(w**2)/np.sum(w)**2
print(f"Kish 가중 설계효과 deff_w={deff_w:.2f}, 유효표본 n_eff={n/deff_w:.0f} (n={n})")

def rq1_mae(act,syn):
    errs=[]
    for v in BIN:
        s=act[[v,"WT"]].dropna(); am=np.average(s[v],weights=s["WT"])
        # 조건부 문항은 그 문항 응답자만으로 셀 점유율을 계산한다
        cw=act[act[v].notna()].groupby(CELL)["WT"].sum(); share=(cw/cw.sum()).to_dict()
        cm={k:g[v].mean() for k,g in syn.groupby(CELL)}
        num=sum(share.get(k,0)*cm[k] for k in cm if k in share and not np.isnan(cm[k]))
        den=sum(share.get(k,0) for k in cm if k in share and not np.isnan(cm[k]))
        errs.append(abs(num/den-am))
    return np.mean(errs)*100

# 가구 군집 부트스트랩 준비
hh_groups={h:idx.to_numpy() for h,idx in a24.groupby("hid").groups.items()}
hh_ids=np.array(list(hh_groups.keys()),dtype=object)
def cluster_resample():
    pick=rng.choice(len(hh_ids),size=len(hh_ids),replace=True)
    rows=np.concatenate([hh_groups[hh_ids[i]] for i in pick])
    return a24.loc[rows]

B=600
sheet_rows=[{"항목":"Kish 설계효과 deff_w","값":round(deff_w,2),"비고":f"가중 불균등(WT {w.min():.2f}~{w.max():.1f}), n={n}"},
            {"항목":"유효표본 n_eff","값":int(round(n/deff_w)),"비고":"n/deff"}]
for m,f in [("Gemini","outputs/synthetic_recoded_gemini.csv"),("EXAONE","outputs/synthetic_recoded_exaone.csv")]:
    syn=pd.read_csv(f,encoding="utf-8-sig")
    pt=rq1_mae(a24,syn)
    boot=[]
    for _ in range(B):
        ab=cluster_resample()
        sb=syn.sample(len(syn),replace=True,random_state=int(rng.integers(1e9)))
        boot.append(rq1_mae(ab,sb))
    lo,hi=np.percentile(boot,[2.5,97.5])
    print(f"{m}: MAE {pt:.1f}%p | 설계기반(가구군집) 95% CI [{lo:.1f}, {hi:.1f}]  )")
    sheet_rows.append({"항목":f"{m} RQ1 MAE CI(설계기반)","값":f"[{lo:.1f}, {hi:.1f}]",
                       "비고":f"가구군집({a24['hid'].nunique()}) 부트스트랩 B={B}; 행단위 CI 는 rq_uncertainty.py 콘솔 출력 참조"})
sheet_rows.append({"항목":"지표당 설계조정 표집오차","값":f"약 {100*np.sqrt(0.25/(n/deff_w)):.2f}%p","비고":"p=0.5, n_eff 기준"})
# 워크북 시트 기록(콘솔 출력과 동일 값; 시트 설계기반_분산 의 배치. 행단위 CI 는 rq_uncertainty.py 의 값을 옮겨 적은 것)
with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    pd.DataFrame(sheet_rows).to_excel(w,sheet_name="설계기반_분산",index=False)
print("워크북 시트 추가: 설계기반_분산")
