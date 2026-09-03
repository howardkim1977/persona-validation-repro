# -*- coding: utf-8 -*-
"""부록 10대 제외 민감도용: 12셀(10대 제외)에서 보정 형태 {lin, quad, nested} 와 실측 직접추정의
30% 층화 200분할 검정 MAE + 미관측 셀 홀드아웃. rr_calibration_forms_extended.py 와 동일 규약(seed 42)."""
import numpy as np, pandas as pd
from rr_common import *

REPS=200; INNER=5; HREPS=50; KEEP=AGEC>0     # 10대(코드 0) 제외
CANDS=["global","age_lin","age_quad","age_sex","age_sex_x"]
def design(form):
    return {"global":np.ones((NC,1)),"age_lin":np.column_stack([np.ones(NC),AGEC]),
            "age_quad":np.column_stack([np.ones(NC),AGEC,AGEC**2]),"age_sex":np.column_stack([np.ones(NC),AGEC,SEXD]),
            "age_sex_x":np.column_stack([np.ones(NC),AGEC,SEXD,AGEC*SEXD])}[form]
def fit_pred(form,bias,av):
    X=design(form); Xa=X[av]; y=bias[av]
    if Xa.shape[0]<=Xa.shape[1]: return np.full(NC,np.nanmean(y) if av.any() else 0.0)
    beta,*_=np.linalg.lstsq(Xa,y,rcond=None); return X@beta
def nested_pred(s,real,cal,rng,v):
    score={c:[] for c in CANDS}
    for _ in range(INNER):
        ic=stratified_split(rng,real,0.5)&cal; iv=cal&~ic
        icc=real.cell_wmean(ic,v); ivc=real.cell_wmean(iv,v); iav=KEEP&~np.isnan(icc)&~np.isnan(s); itv=KEEP&~np.isnan(ivc)&~np.isnan(s)
        if itv.sum()==0 or iav.sum()==0: continue
        for c in CANDS: score[c].append(np.mean(np.abs((s-fit_pred(c,s-icc,iav))-ivc)[itv]))
    best=min(CANDS,key=lambda c:np.mean(score[c]) if score[c] else np.inf)
    cc=real.cell_wmean(cal,v); av=KEEP&~np.isnan(cc)&~np.isnan(s); return fit_pred(best,s-cc,av)
def fit_rate_reg(rate,wcell,av):
    if av.sum()>=3:
        X=np.column_stack([np.ones(av.sum()),AGEC[av],SEXD[av]]); W=np.sqrt(np.maximum(wcell[av],1e-9))
        beta,*_=np.linalg.lstsq(X*W[:,None],rate[av]*W,rcond=None); return np.clip(beta[0]+beta[1]*AGEC+beta[2]*SEXD,0,1)
    return np.full(NC,np.nanmean(rate[av]) if av.any() else np.nan)

real=Real(load_real(2024)); SYN={m:syn_cell_means(load_syn(f)) for m,f in SYN_FILES.items()}
rng=np.random.default_rng(SEED); E={m:{k:[] for k in ["unc","lin","quad","nested","real_dir"]} for m in SYN}
for _ in range(REPS):
    cal=stratified_split(rng,real,0.30); tst=~cal
    for m,sc in SYN.items():
        e={k:[] for k in E[m]}
        for v in BIN:
            s=sc[v]; cc=real.cell_wmean(cal,v); tc=real.cell_wmean(tst,v); gm=real.grand_wmean(cal,v)
            tv=KEEP&~np.isnan(tc)&~np.isnan(s); av=tv&~np.isnan(cc); bias=s-cc
            e["unc"]+=list(np.abs(s-tc)[tv]); e["lin"]+=list(np.abs((s-fit_pred("age_lin",bias,av))-tc)[tv])
            e["quad"]+=list(np.abs((s-fit_pred("age_quad",bias,av))-tc)[tv]); e["nested"]+=list(np.abs((s-nested_pred(s,real,cal,rng,v))-tc)[tv])
            e["real_dir"]+=list(np.abs(np.where(np.isnan(cc),gm,cc)-tc)[tv])
        for k in E[m]: E[m][k].append(np.mean(e[k])*100)
rows=[{"모델":m,**{k+"%p":round(np.mean(v),2) for k,v in E[m].items()}} for m in SYN]
# 미관측 셀 홀드아웃(10대 제외 12셀)
rng=np.random.default_rng(SEED); full=np.ones(real.n,bool); FC={v:real.cell_wmean(full,v) for v in BIN}
for m,sc in SYN.items():
    e={k:[] for k in ["lin","quad","nested","real_reg"]}
    for j in np.where(KEEP)[0]:
        for _ in range(HREPS):
            cal=stratified_split(rng,real,0.30)&(real.cell!=j); wcell=np.bincount(real.cell[cal],weights=real.wt[cal],minlength=NC)
            for v in BIN:
                t=FC[v][j]; s=sc[v]
                if np.isnan(t) or np.isnan(s[j]): continue
                cc=real.cell_wmean(cal,v); av=KEEP&~np.isnan(cc)&~np.isnan(s); av[j]=False; bias=s-cc
                e["lin"].append(abs((s[j]-fit_pred("age_lin",bias,av)[j])-t)); e["quad"].append(abs((s[j]-fit_pred("age_quad",bias,av)[j])-t))
                e["nested"].append(abs((s[j]-nested_pred(s,real,cal,rng,v)[j])-t)); e["real_reg"].append(abs(fit_rate_reg(cc,wcell,av)[j]-t))
    rows.append({"모델":m+" (셀홀드아웃)",**{k+"%p":round(np.mean(v)*100,2) for k,v in e.items()}})
df=pd.DataFrame(rows); write_sheets({"심사_십대제외_보정형태":df}); print(df.to_string(index=False))
