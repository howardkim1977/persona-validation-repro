# -*- coding: utf-8 -*-
"""R2-8: 표본 불확실성과 생성 불확실성의 결합 — 계층 부트스트랩.
EXAONE 전체 패널 3회 독립 생성(k1·k2·k3, 동일 페르소나)을 재료로
  (a) 단일 패스 행 재표집(본문 RQ1 CI 규약: 실측 가구군집 + 합성 행)
  (b) 계층: 페르소나 재표집 후 페르소나마다 3개 패스 중 1개를 무작위 선택(표집+생성 결합)
  (c) 페르소나 재표집 + 3패스 평균(생성 노이즈 평균화)
의 RQ1 MAE 95% CI 를 비교한다. B=600, seed 42. (Gemini 는 순서 실험 F1~F3 부분표본으로 rr_order_analysis.py 에서 보고)"""
import numpy as np, pandas as pd
from rr_common import *
from recode import recode

B=600; rng=np.random.default_rng(SEED)
real=Real(load_real(2024))
def load_pass(path):
    d=pd.read_csv(path,encoding="utf-8-sig")
    if "_error" in d: d=d[d["_error"].isna()]
    r=recode(d); r["_idx"]=d["_idx"].values; r=r[r["연령대"].isin(AGES)]
    r["_cell"]=[CIDX[(g,a)] for g,a in zip(r["성별"],r["연령대"])]; return r.set_index("_idx")
P=[load_pass(f) for f in ["outputs/synthetic_exaone.csv","outputs/synthetic_exaone_k2.csv","outputs/synthetic_exaone_k3.csv"]]
common=sorted(set(P[0].index)&set(P[1].index)&set(P[2].index)); print(f"3패스 공통 유효 페르소나 {len(common)}")
cell=P[0].loc[common,"_cell"].to_numpy()
Y=np.stack([np.stack([p.loc[common,v].to_numpy(float) for v in BIN],axis=1) for p in P])   # (3, n, 8)
n=len(common)

def mae_from(idx_r, ymat, idx_p):
    w=real.wt[idx_r]; c=real.cell[idx_r]; share=np.bincount(c,weights=w,minlength=NC); share=share/share.sum()
    errs=[]
    for j,v in enumerate(BIN):
        yr=real.Y[v][idx_r]; ok=~np.isnan(yr); ar=np.average(yr[ok],weights=w[ok])
        ys=ymat[idx_p,j]; cs=cell[idx_p]; ok2=~np.isnan(ys)
        num=np.bincount(cs[ok2],weights=ys[ok2],minlength=NC); den=np.bincount(cs[ok2],minlength=NC)
        with np.errstate(invalid="ignore"): cm=np.where(den>0,num/den,np.nan)
        errs.append(abs(post_stratified_rate(share,cm)-ar))
    return np.mean(errs)*100
full=np.arange(real.n); allp=np.arange(n)
pt=[mae_from(full,Y[k],allp) for k in range(3)]; pt_avg=mae_from(full,Y.mean(axis=0),allp)
res={"a_단일패스(k1)":[],"b_계층(페르소나×패스)":[],"c_페르소나재표집_3패스평균":[]}
for _ in range(B):
    ir=household_resample_index(rng,real); ip=rng.integers(0,n,n)
    res["a_단일패스(k1)"].append(mae_from(ir,Y[0],ip))
    pick=rng.integers(0,3,n); ymix=Y[pick,ip,:]; res["b_계층(페르소나×패스)"].append(mae_from(ir,ymix,np.arange(n)))
    res["c_페르소나재표집_3패스평균"].append(mae_from(ir,Y.mean(axis=0),ip))
rows=[]
for k,v in res.items():
    lo,hi=np.percentile(v,[2.5,97.5]); rows.append({"설계":k,"점추정MAE%p":round(pt[0] if k.startswith("a") else (pt_avg if k.startswith("c") else np.mean(pt)),2),
                                                   "CI_하한":round(lo,2),"CI_상한":round(hi,2),"CI폭":round(hi-lo,2),"부트스트랩SD":round(np.std(v),3)})
rows.append({"설계":"참고: 패스별 점추정 k1/k2/k3","점추정MAE%p":"/".join(f"{x:.2f}" for x in pt)})
df=pd.DataFrame(rows); write_sheets({"심사_계층부트스트랩_EXAONE":df}); print(df.to_string(index=False))
