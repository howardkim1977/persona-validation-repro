# -*- coding: utf-8 -*-
"""R2-7: 극소 보정률 구간의 정밀화(교차점 주변).

보정률 1/2/3/5/10% × 200회 층화 개인 분할. 분할마다 보정셀 표본수 분포(최소·중앙값·빈 셀 수),
방법별 검정 MAE, 방법별 최우수 빈도, 합성보정−실측 짝 차이의 분할분위 구간,
빈 셀 대체 규칙 민감도(전체평균 대체 / 실측회귀 예측 대체 / 빈 셀 제외 평가)를 기록한다."""
import numpy as np, pandas as pd
from rr_common import *

FRACS=[0.01,0.02,0.03,0.05,0.10]; REPS=200
real=Real(load_real(2024)); SYN={m:syn_cell_means(load_syn(f)) for m,f in SYN_FILES.items()}

def fit_bias_reg(bias,av):
    if av.sum()>=3: sl,ic=np.polyfit(AGEC[av],bias[av],1); return sl*AGEC+ic
    return np.full(NC,np.nanmean(bias[av]) if av.any() else 0.0)
def fit_rate_reg(rate,wcell,av):
    if av.sum()>=3:
        X=np.column_stack([np.ones(av.sum()),AGEC[av],SEXD[av]]); W=np.sqrt(np.maximum(wcell[av],1e-9))
        beta,*_=np.linalg.lstsq(X*W[:,None],rate[av]*W,rcond=None); return np.clip(beta[0]+beta[1]*AGEC+beta[2]*SEXD,0,1)
    return np.full(NC,np.nanmean(rate[av]) if av.any() else np.nan)

rows=[]
for frac in FRACS:
    rng=np.random.default_rng(SEED)
    stat={"n_cal":[],"cell_min":[],"cell_med":[],"empty":[]}
    E={m:{k:[] for k in ["syn_reg","real_dir","real_dir_regfb","real_reg","real_gm","syn_reg_ne","real_dir_ne"]} for m in SYN}
    for _ in range(REPS):
        cal=stratified_split(rng,real,frac); tst=~cal; n=real.cell_n(cal); wcell=np.bincount(real.cell[cal],weights=real.wt[cal],minlength=NC)
        stat["n_cal"].append(cal.sum()); stat["cell_min"].append(n.min()); stat["cell_med"].append(np.median(n)); stat["empty"].append((n==0).sum())
        for m,sc in SYN.items():
            e={k:[] for k in E[m]}
            for v in BIN:
                cc=real.cell_wmean(cal,v); tc=real.cell_wmean(tst,v); gm=real.grand_wmean(cal,v); s=sc[v]
                tv=~np.isnan(tc)&~np.isnan(s); av=tv&~np.isnan(cc)
                pred=fit_bias_reg(s-cc,av); rreg=fit_rate_reg(cc,wcell,av)
                rdir=np.where(np.isnan(cc),gm,cc); rdir2=np.where(np.isnan(cc),rreg,cc)
                e["syn_reg"]+=list(np.abs((s-pred)-tc)[tv]); e["real_dir"]+=list(np.abs(rdir-tc)[tv])
                e["real_dir_regfb"]+=list(np.abs(rdir2-tc)[tv]); e["real_reg"]+=list(np.abs(rreg-tc)[tv]); e["real_gm"]+=list(np.abs(gm-tc)[tv])
                e["syn_reg_ne"]+=list(np.abs((s-pred)-tc)[av]); e["real_dir_ne"]+=list(np.abs(cc-tc)[av])
            for k in E[m]: E[m][k].append(np.mean(e[k])*100)
    for m in SYN:
        A={k:np.array(v) for k,v in E[m].items()}
        d1=A["syn_reg"]-A["real_dir"]; d2=A["syn_reg"]-A["real_reg"]; best_real=np.minimum(A["real_dir"],A["real_reg"])
        r={"보정률":frac,"모델":m,"보정셋n(평균)":round(np.mean(stat["n_cal"])),"셀n_최소(평균)":round(np.mean(stat["cell_min"]),1),
           "셀n_중앙값(평균)":round(np.mean(stat["cell_med"]),1),"빈셀수(평균)":round(np.mean(stat["empty"]),2),
           "빈셀발생분할비율%":round(100*np.mean(np.array(stat["empty"])>0),1)}
        for k in ["syn_reg","real_dir","real_dir_regfb","real_reg","real_gm"]: r[k+"_MAE%p"]=round(A[k].mean(),2)
        r["Δ(syn_reg−real_dir)%p"]=round(d1.mean(),2); r["Δ1_CI"]="[%.2f, %.2f]"%tuple(np.percentile(d1,[2.5,97.5]))
        r["Δ(syn_reg−real_reg)%p"]=round(d2.mean(),2); r["Δ2_CI"]="[%.2f, %.2f]"%tuple(np.percentile(d2,[2.5,97.5]))
        r["합성보정<실측직접 빈도%"]=round(100*(A["syn_reg"]<A["real_dir"]).mean(),1)
        r["합성보정<실측회귀 빈도%"]=round(100*(A["syn_reg"]<A["real_reg"]).mean(),1)
        r["합성보정<최우수실측 빈도%"]=round(100*(A["syn_reg"]<best_real).mean(),1)
        r["빈셀제외_syn_reg%p"]=round(A["syn_reg_ne"].mean(),2); r["빈셀제외_real_dir%p"]=round(A["real_dir_ne"].mean(),2)
        rows.append(r)
        print(f"[f={frac:.2f} {m}] n_cal≈{r['보정셋n(평균)']} 빈셀 {r['빈셀수(평균)']} | syn_reg {r['syn_reg_MAE%p']} real_dir {r['real_dir_MAE%p']} "
              f"real_reg {r['real_reg_MAE%p']} | Δ1 {r['Δ(syn_reg−real_dir)%p']} {r['Δ1_CI']} | 최우수실측 대비 승률 {r['합성보정<최우수실측 빈도%']}%")
write_sheets({"심사_학습곡선_정밀":pd.DataFrame(rows)})
