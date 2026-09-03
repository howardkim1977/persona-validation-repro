# -*- coding: utf-8 -*-
"""R2-1/m-a/m-c: 모델 간 MAE 차이의 짝 부트스트랩 CI + 지표별 Holm 보정 + Spearman 상관.

동일한 실측 가구 군집 재표집 복제 안에서 두 패널의 MAE를 함께 계산해 차이의 분포를 얻는다
(주변 CI 비중첩 판단을 대체). 합성 패널은 독립 생성이므로 행 단위 재표집. B=600, seed 42."""
import numpy as np, pandas as pd
from scipy.stats import spearmanr, pearsonr
from rr_common import *

B=600
rng=np.random.default_rng(SEED)

def syn_arrays(path, vars_):
    s=load_syn(path); return s["_cell"].to_numpy(), {v:s[v].to_numpy(float) for v in vars_}, len(s)

def real_stats(real, idx, vars_):
    """재표집 행 인덱스(중복 허용)로 가중 셀 점유율·전체 가중률 계산."""
    w=real.wt[idx]; c=real.cell[idx]
    share=np.bincount(c,weights=w,minlength=NC); share=share/share.sum()
    rates={}
    for v in vars_:
        y=real.Y[v][idx]; ok=~np.isnan(y); rates[v]=np.average(y[ok],weights=w[ok])
    return share, rates

def syn_rates(cell, Y, idx, share, vars_):
    out={}
    for v in vars_:
        y=Y[v][idx]; c=cell[idx]; ok=~np.isnan(y)
        num=np.bincount(c[ok],weights=y[ok],minlength=NC); den=np.bincount(c[ok],minlength=NC)
        with np.errstate(invalid="ignore"): cm=np.where(den>0,num/den,np.nan)
        out[v]=post_stratified_rate(share,cm)
    return out

def compare(label, name, fa, fb, real, vars_=BIN):
    ca,Ya,na=syn_arrays(fa,vars_); cb,Yb,nb=syn_arrays(fb,vars_)
    full=np.arange(real.n); share,rr=real_stats(real,full,vars_)
    pa=syn_rates(ca,Ya,np.arange(na),share,vars_); pb=syn_rates(cb,Yb,np.arange(nb),share,vars_)
    ea={v:abs(pa[v]-rr[v])*100 for v in vars_}; eb={v:abs(pb[v]-rr[v])*100 for v in vars_}
    pt=np.mean(list(ea.values()))-np.mean(list(eb.values()))
    D=[]; Dv={v:[] for v in vars_}; corr={"pearson_a":[],"pearson_b":[],"spearman_a":[],"spearman_b":[]}
    for _ in range(B):
        idx=household_resample_index(rng,real); sh,r=real_stats(real,idx,vars_)
        qa=syn_rates(ca,Ya,rng.integers(0,na,na),sh,vars_); qb=syn_rates(cb,Yb,rng.integers(0,nb,nb),sh,vars_)
        da=[abs(qa[v]-r[v])*100 for v in vars_]; db=[abs(qb[v]-r[v])*100 for v in vars_]
        D.append(np.mean(da)-np.mean(db))
        for v,x,y in zip(vars_,da,db): Dv[v].append(x-y)
        rv=[r[v] for v in vars_]
        corr["pearson_a"].append(pearsonr(rv,[qa[v] for v in vars_])[0]); corr["pearson_b"].append(pearsonr(rv,[qb[v] for v in vars_])[0])
        corr["spearman_a"].append(spearmanr(rv,[qa[v] for v in vars_])[0]); corr["spearman_b"].append(spearmanr(rv,[qb[v] for v in vars_])[0])
    D=np.array(D); lo,hi=np.percentile(D,[2.5,97.5])
    p=2*min((D<=0).mean(),(D>=0).mean()); p=max(p,1/B)
    rows=[{"비교":label,"대상":name,"지표":"MAE 전체","A_MAE%p":round(np.mean(list(ea.values())),2),
           "B_MAE%p":round(np.mean(list(eb.values())),2),"차이(A-B)%p":round(pt,2),
           "CI_하한":round(lo,2),"CI_상한":round(hi,2),"부트스트랩p":round(p,4),"Holm_p":np.nan}]
    pv=[]
    for v in vars_:
        d=np.array(Dv[v]); l,h=np.percentile(d,[2.5,97.5]); pp=max(2*min((d<=0).mean(),(d>=0).mean()),1/B); pv.append(pp)
        rows.append({"비교":label,"대상":name,"지표":v,"A_MAE%p":round(ea[v],2),"B_MAE%p":round(eb[v],2),
                     "차이(A-B)%p":round(ea[v]-eb[v],2),"CI_하한":round(l,2),"CI_상한":round(h,2),"부트스트랩p":round(pp,4)})
    hp=holm(pv)
    for i,r in enumerate(rows[1:]): r["Holm_p"]=round(hp[i],4)
    rv=[rr[v] for v in vars_]
    crow={"비교":label,"대상":name}
    for tag,q in [("A",pa),("B",pb)]:
        qq=[q[v] for v in vars_]
        crow[f"{tag}_Pearson"]=round(pearsonr(rv,qq)[0],3); crow[f"{tag}_Spearman"]=round(spearmanr(rv,qq)[0],3)
    for k in corr:
        l,h=np.percentile(corr[k],[2.5,97.5]); crow[k.replace("_a","_A").replace("_b","_B")+"_CI"]=f"[{l:.3f}, {h:.3f}]"
    print(f"[{label} | {name}] ΔMAE(A−B)={pt:+.2f} pp, 95% CI [{lo:.2f}, {hi:.2f}], p={p:.4f} | "
          f"Pearson A {crow['A_Pearson']} B {crow['B_Pearson']} | Spearman A {crow['A_Spearman']} B {crow['B_Spearman']}")
    return rows, crow

r24=Real(load_real(2024)); r25=Real(load_real(2025))
G,E=SYN_FILES["Gemini"],SYN_FILES["EXAONE"]
jobs=[("2024 주분석(t=1.0)","Gemini − EXAONE",G,E,r24),
      ("2024 온도 강건성","Gemini t1.0 − t0.7",G,"outputs/synthetic_recoded_gemini_t07.csv",r24),
      ("2024 온도 강건성","EXAONE t1.0 − t0.7",E,"outputs/synthetic_recoded_exaone_t07.csv",r24),
      ("2025 문항셋","Gemini − EXAONE","outputs/synthetic_recoded_2025_gemini.csv","outputs/synthetic_recoded_2025_exaone.csv",r25)]
allrows=[]; crows=[]
for lab,name,fa,fb,real in jobs:
    rows,crow=compare(lab,name,fa,fb,real); allrows+=rows; crows.append(crow)

# 구성개념 평균(1–5점) 상관: Pearson·Spearman(2024)
rc=Real(load_real(2024),vars_=CON); s_g=load_syn(G); s_e=load_syn(E)
share=rc.cell_share(); real_means=[rc.overall_wmean(v) for v in CON]
con_rows=[]
for name,s in [("Gemini",s_g),("EXAONE",s_e)]:
    cm=syn_cell_means(s,CON); q=[post_stratified_rate(share,cm[v]) for v in CON]
    con_rows.append({"모델":name,"Pearson_구성개념":round(pearsonr(real_means,q)[0],3),
                     "Spearman_구성개념":round(spearmanr(real_means,q)[0],3),"n_구성개념":len(CON)})
    print(f"[구성개념 {name}] Pearson {con_rows[-1]['Pearson_구성개념']} Spearman {con_rows[-1]['Spearman_구성개념']}")
write_sheets({"심사_짝부트스트랩":pd.DataFrame(allrows),"심사_상관_Spearman":pd.DataFrame(crows),
              "심사_상관_구성개념":pd.DataFrame(con_rows)})
