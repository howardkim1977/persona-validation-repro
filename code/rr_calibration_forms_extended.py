# -*- coding: utf-8 -*-
"""R2-2/R2-6/R2-7 통합: 보정 형태 {global, age_lin(발표), age_quad, nested} 를
  (1) 학습곡선(개인 층화 / 가구 군집 분할 × 보정률 1·2·3·5·10·20·30% × 200회)
  (2) 셀 전체 홀드아웃(미관측 세그먼트 외삽; 14셀 × 50회)
  (3) 시점 홀드아웃(2024 전체에서 학습 → 2025 패널을 2025 기준으로 검정)
에 일관되게 적용한다. nested = 보정 자료 내부 5회 50/50 재분할로 {global, age_lin, age_quad, age_sex, age_sex_x}
중 내부 검정 MAE 최소 형태를 고른 뒤 보정 자료 전체에 재적합(선택이 검정 자료를 보지 않음).
가구 분할에서는 빈 셀 통계와 실측 직접추정의 빈 셀 대체 규칙(전체평균 / 실측회귀 예측) 민감도도 기록한다."""
import numpy as np, pandas as pd
from rr_common import *

FRACS=[0.01,0.02,0.03,0.05,0.10,0.20,0.30]; REPS=200; INNER=5; HREPS=50
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
    """보정 마스크 cal 내부 재분할로 형태 선택 → cal 전체 재적합 예측 반환(선택 형태 포함)."""
    score={c:[] for c in CANDS}
    for _ in range(INNER):
        ic=stratified_split(rng,real,0.5)&cal; iv=cal&~ic
        icc=real.cell_wmean(ic,v); ivc=real.cell_wmean(iv,v); iav=~np.isnan(icc)&~np.isnan(s); itv=~np.isnan(ivc)&~np.isnan(s)
        if itv.sum()==0 or iav.sum()==0: continue
        for c in CANDS: score[c].append(np.mean(np.abs((s-fit_pred(c,s-icc,iav))-ivc)[itv]))
    best=min(CANDS,key=lambda c:np.mean(score[c]) if score[c] else np.inf)
    cc=real.cell_wmean(cal,v); av=~np.isnan(cc)&~np.isnan(s)
    return fit_pred(best,s-cc,av),best
def fit_rate_reg(rate,wcell,av):
    if av.sum()>=3:
        X=np.column_stack([np.ones(av.sum()),AGEC[av],SEXD[av]]); W=np.sqrt(np.maximum(wcell[av],1e-9))
        beta,*_=np.linalg.lstsq(X*W[:,None],rate[av]*W,rcond=None); return np.clip(beta[0]+beta[1]*AGEC+beta[2]*SEXD,0,1)
    return np.full(NC,np.nanmean(rate[av]) if av.any() else np.nan)
def household_split(rng,real,frac):
    uniq=np.unique(real.hh); rng.shuffle(uniq); return np.isin(real.hh,uniq[:int(len(uniq)*frac)])

real=Real(load_real(2024)); SYN={m:syn_cell_means(load_syn(f)) for m,f in SYN_FILES.items()}
FORMS=["syn_unc","syn_glob","syn_lin","syn_quad","syn_nested","real_dir","real_dir_regfb","real_reg","real_gm"]

# ── (1) 학습곡선 ──
rows=[]
for mode in ["individual","household"]:
    for frac in FRACS:
        rng=np.random.default_rng(SEED)
        E={m:{k:[] for k in FORMS} for m in SYN}; sel={m:{c:0 for c in CANDS} for m in SYN}
        st={"n":[],"cmin":[],"empty":[]}
        for _ in range(REPS):
            cal=stratified_split(rng,real,frac) if mode=="individual" else household_split(rng,real,frac); tst=~cal
            n=real.cell_n(cal); wcell=np.bincount(real.cell[cal],weights=real.wt[cal],minlength=NC)
            st["n"].append(cal.sum()); st["cmin"].append(n.min()); st["empty"].append((n==0).sum())
            for m,sc in SYN.items():
                e={k:[] for k in FORMS}
                for v in BIN:
                    s=sc[v]; cc=real.cell_wmean(cal,v); tc=real.cell_wmean(tst,v); gm=real.grand_wmean(cal,v)
                    tv=~np.isnan(tc)&~np.isnan(s); av=tv&~np.isnan(cc); bias=s-cc
                    b=np.nanmean(bias[av]) if av.any() else 0.0
                    p_lin=fit_pred("age_lin",bias,av); p_quad=fit_pred("age_quad",bias,av)
                    p_nest,best=nested_pred(s,real,cal,rng,v); sel[m][best]+=1
                    rreg=fit_rate_reg(cc,wcell,av); rdir=np.where(np.isnan(cc),gm,cc); rdir2=np.where(np.isnan(cc),rreg,cc)
                    for k,pred in [("syn_unc",0),("syn_glob",b),("syn_lin",p_lin),("syn_quad",p_quad),("syn_nested",p_nest)]:
                        e[k]+=list(np.abs((s-pred)-tc)[tv])
                    e["real_dir"]+=list(np.abs(rdir-tc)[tv]); e["real_dir_regfb"]+=list(np.abs(rdir2-tc)[tv])
                    e["real_reg"]+=list(np.abs(rreg-tc)[tv]); e["real_gm"]+=list(np.abs(gm-tc)[tv])
                for k in FORMS: E[m][k].append(np.mean(e[k])*100)
        for m in SYN:
            A={k:np.array(v) for k,v in E[m].items()}; best_real=np.minimum(A["real_dir"],A["real_reg"])
            r={"분할":mode,"보정률":frac,"모델":m,"보정셋n":round(np.mean(st["n"])),"셀n최소(평균)":round(np.mean(st["cmin"]),1),
               "빈셀수(평균)":round(np.mean(st["empty"]),2),"빈셀발생분할%":round(100*np.mean(np.array(st["empty"])>0),1)}
            for k in FORMS: r[k+"%p"]=round(A[k].mean(),2)
            for k in ["syn_lin","syn_quad","syn_nested"]:
                d=A[k]-best_real; lo,hi=np.percentile(d,[2.5,97.5])
                r[f"Δ({k}−최우수실측)"]=round(d.mean(),2); r[f"Δ({k})_CI"]=f"[{lo:.2f}, {hi:.2f}]"; r[f"{k}<최우수실측%"]=round(100*(d<0).mean(),1)
            tot=sum(sel[m].values()); r["nested선택: quad%"]=round(100*sel[m]["age_quad"]/tot,1); r["nested선택: lin%"]=round(100*sel[m]["age_lin"]/tot,1)
            rows.append(r)
            print(f"[{mode} f={frac:.2f} {m}] n={r['보정셋n']} 빈셀 {r['빈셀수(평균)']} | lin {r['syn_lin%p']} quad {r['syn_quad%p']} nested {r['syn_nested%p']} "
                  f"| real_dir {r['real_dir%p']} real_reg {r['real_reg%p']} | nested<최우수실측 {r['syn_nested<최우수실측%']}% | quad선택 {r['nested선택: quad%']}%",flush=True)
lc=pd.DataFrame(rows)

# ── (2) 셀 전체 홀드아웃 ──
rng=np.random.default_rng(SEED); hrows=[]; full=np.ones(real.n,bool)
FC={v:real.cell_wmean(full,v) for v in BIN}
for m,sc in SYN.items():
    e={k:[] for k in ["syn_unc","syn_lin","syn_quad","syn_nested","real_reg","real_gm"]}
    for j in range(NC):
        for _ in range(HREPS):
            cal=stratified_split(rng,real,0.30); cal&=(real.cell!=j)
            wcell=np.bincount(real.cell[cal],weights=real.wt[cal],minlength=NC)
            for v in BIN:
                t=FC[v][j]; s=sc[v]
                if np.isnan(t) or np.isnan(s[j]): continue
                cc=real.cell_wmean(cal,v); gm=real.grand_wmean(cal,v); av=~np.isnan(cc)&~np.isnan(s); av[j]=False; bias=s-cc
                p_nest,_=nested_pred(s,real,cal,rng,v)
                e["syn_unc"].append(abs(s[j]-t)); e["syn_lin"].append(abs((s[j]-fit_pred("age_lin",bias,av)[j])-t))
                e["syn_quad"].append(abs((s[j]-fit_pred("age_quad",bias,av)[j])-t)); e["syn_nested"].append(abs((s[j]-p_nest[j])-t))
                e["real_reg"].append(abs(fit_rate_reg(cc,wcell,av)[j]-t)); e["real_gm"].append(abs(gm-t))
    hrows.append({"모델":m,**{k+"%p":round(np.mean(v)*100,2) for k,v in e.items()}})
    print(f"[셀홀드아웃 {m}] "+" ".join(f"{k}={v}" for k,v in hrows[-1].items() if k!='모델'),flush=True)

# ── (3) 시점 홀드아웃: 2024 전체 학습 → 2025 검정 ──
r25=Real(load_real(2025)); full25=np.ones(r25.n,bool); trows=[]
S25={"Gemini":syn_cell_means(load_syn("outputs/synthetic_recoded_2025_gemini.csv")),"EXAONE":syn_cell_means(load_syn("outputs/synthetic_recoded_2025_exaone.csv"))}
rng=np.random.default_rng(SEED)
for m in SYN:
    e={k:[] for k in ["unc","glob","lin","quad","nested","gm25","prev24"]}; picks={c:0 for c in CANDS}
    for v in BIN:
        s24=SYN[m][v]; s25=S25[m][v]; a24c=real.cell_wmean(full,v); a25c=r25.cell_wmean(full25,v); g25=r25.grand_wmean(full25,v)
        av=~np.isnan(a24c)&~np.isnan(s24); tv=~np.isnan(a25c)&~np.isnan(s25); bias=s24-a24c
        b=np.nanmean(bias[av]); p_nest,best=nested_pred(s24,real,full,rng,v); picks[best]+=1
        for k,pred in [("unc",0),("glob",b),("lin",fit_pred("age_lin",bias,av)),("quad",fit_pred("age_quad",bias,av)),("nested",p_nest)]:
            e[k]+=list(np.abs((s25-pred)-a25c)[tv])
        e["gm25"]+=list(np.abs(g25-a25c)[tv]); e["prev24"]+=list(np.abs(a24c-a25c)[tv&~np.isnan(a24c)])
    trows.append({"모델":m,**{k+"%p":round(np.mean(v)*100,2) for k,v in e.items()},"nested선택":str(picks)})
    print(f"[시점홀드아웃 {m}] "+" ".join(f"{k}={v}" for k,v in trows[-1].items() if k!='모델'),flush=True)
write_sheets({"심사_보정형태_학습곡선":lc,"심사_보정형태_셀홀드아웃":pd.DataFrame(hrows),"심사_보정형태_시점홀드아웃":pd.DataFrame(trows)})
