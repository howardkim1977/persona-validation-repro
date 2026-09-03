# -*- coding: utf-8 -*-
"""R2-6 보완: 경험적 베이즈 부분풀링 보정의 보정률 곡선(1·2·3·5·10·30%, 개인 층화 200분할).
셀 편향 b_c 를 연령 선형 적합선으로 수축: b*_c = λ_c b_c + (1-λ_c) fit_c, λ_c = τ²/(τ²+σ²_c),
σ²_c = 보정셀 평균의 표집분산(p(1-p)/n_eff), τ² = 잔차분산 − 평균 σ². 셀이 크면 λ→1(직접추정으로 수렴)."""
import numpy as np, pandas as pd
from rr_common import *
FRACS=[0.01,0.02,0.03,0.05,0.10,0.20,0.30]; REPS=200
real=Real(load_real(2024)); SYN={m:syn_cell_means(load_syn(f)) for m,f in SYN_FILES.items()}
def rreg(rate,wcell,av):
    """실측 단독 연령+성별 가중 선형회귀 예측(순수 실측 수축 목표)."""
    if av.sum()>=3:
        X=np.column_stack([np.ones(av.sum()),AGEC[av],SEXD[av]]); W=np.sqrt(np.maximum(wcell[av],1e-9))
        beta,*_=np.linalg.lstsq(X*W[:,None],rate[av]*W,rcond=None); return np.clip(beta[0]+beta[1]*AGEC+beta[2]*SEXD,0,1)
    return np.full(NC,np.nanmean(rate[av]) if av.any() else np.nan)
def lin(bias,av):
    if av.sum()>=3: sl,ic=np.polyfit(AGEC[av],bias[av],1); return sl*AGEC+ic
    return np.full(NC,np.nanmean(bias[av]) if av.any() else 0.0)
rows=[]
for frac in FRACS:
    rng=np.random.default_rng(SEED); E={m:{"eb":[],"eb_real":[],"lin":[],"dir":[],"lam":[]} for m in SYN}
    for _ in range(REPS):
        cal=stratified_split(rng,real,frac); tst=~cal; neff=real.cell_neff(cal); wcell=np.bincount(real.cell[cal],weights=real.wt[cal],minlength=NC)
        for m,sc in SYN.items():
            e={"eb":[],"eb_real":[],"lin":[],"dir":[],"lam":[]}
            for v in BIN:
                s=sc[v]; cc=real.cell_wmean(cal,v); tc=real.cell_wmean(tst,v); gm=real.grand_wmean(cal,v)
                av=~np.isnan(cc)&~np.isnan(s); tv=~np.isnan(tc)&~np.isnan(s); bias=s-cc
                fit=lin(bias,av); sig2=np.where(av,np.maximum(cc*(1-cc),1e-4)/np.maximum(neff,1),np.nan)
                res=bias-fit; tau2=max(0.0,np.nanvar(res[av],ddof=1)-np.nanmean(sig2[av])) if av.sum()>2 else 0.0
                lam=np.where(av,tau2/(tau2+np.where(np.isnan(sig2),1,sig2)+1e-12),0.0)
                eb=np.where(av,lam*bias+(1-lam)*fit,fit)
                e["eb"]+=list(np.abs((s-eb)-tc)[tv]); e["lin"]+=list(np.abs((s-fit)-tc)[tv])
                fr=rreg(cc,wcell,av); resr=cc-fr; tau2r=max(0.0,np.nanvar(resr[av],ddof=1)-np.nanmean(sig2[av])) if av.sum()>2 else 0.0
                lamr=np.where(av,tau2r/(tau2r+np.where(np.isnan(sig2),1,sig2)+1e-12),0.0); ebr=np.where(av,lamr*cc+(1-lamr)*fr,fr)
                e["eb_real"]+=list(np.abs(ebr-tc)[tv])
                e["dir"]+=list(np.abs(np.where(np.isnan(cc),gm,cc)-tc)[tv]); e["lam"]+=list(lam[av])
            for k in ["eb","eb_real","lin","dir"]: E[m][k].append(np.mean(e[k])*100)
            E[m]["lam"].append(np.mean(e["lam"]))
    for m in SYN:
        r={"보정률":frac,"모델":m,"EB풀링_MAE%p":round(np.mean(E[m]["eb"]),2),"순수실측EB_MAE%p":round(np.mean(E[m]["eb_real"]),2),"선형_MAE%p":round(np.mean(E[m]["lin"]),2),
           "실측직접_MAE%p":round(np.mean(E[m]["dir"]),2),"평균수축가중λ":round(np.mean(E[m]["lam"]),3)}
        rows.append(r); print(r,flush=True)
write_sheets({"심사_EB풀링곡선":pd.DataFrame(rows)})
