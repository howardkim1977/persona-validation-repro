# -*- coding: utf-8 -*-
"""R2-2/R2-6: 연령회귀 보정의 세부와 민감도.

200회 층화 30/70 분할(rq_uncertainty.py 와 같은 규약, seed 42)마다 지표별로
  global    전역 가산 편향
  age_lin   연령 선형(발표 프로토콜; 비가중 최소제곱)
  age_lin_w 연령 선형, 보정셀 유효표본수 가중
  age_quad  연령 2차
  age_sex   연령 + 성별
  age_sex_x 연령 + 성별 + 연령×성별
  eb_pool   경험적 베이즈 부분풀링(셀 편향을 age_lin 적합선으로 수축; 수축량 = 표집분산 대비 셀간 분산)
  nested    보정셋 내부 5회 50/50 재분할로 {global, age_lin, age_quad, age_sex, age_sex_x} 중 선택 후 전체 보정셋에 재적합
을 적합해 검정셋 MAE, 계수 분포, 잔차 진단, 보정 추정치의 분할 간 변동을 기록한다."""
import numpy as np, pandas as pd
from rr_common import *

REPS=200; FRAC=0.30; INNER=5
FORMS=["global","age_lin","age_lin_w","age_quad","age_sex","age_sex_x","eb_pool","nested"]
CANDS=["global","age_lin","age_quad","age_sex","age_sex_x"]

def design(form):
    if form=="global":   return np.ones((NC,1))
    if form in("age_lin","age_lin_w"): return np.column_stack([np.ones(NC),AGEC])
    if form=="age_quad": return np.column_stack([np.ones(NC),AGEC,AGEC**2])
    if form=="age_sex":  return np.column_stack([np.ones(NC),AGEC,SEXD])
    if form=="age_sex_x":return np.column_stack([np.ones(NC),AGEC,SEXD,AGEC*SEXD])
    raise ValueError(form)

def fit_pred(form,bias,av,neff=None):
    """av 셀의 편향에 form 을 적합해 전 셀 예측 편향 반환(계수 포함)."""
    X=design(form); Xa=X[av]; y=bias[av]
    if Xa.shape[0]<=Xa.shape[1]: b=np.full(NC,np.nanmean(y)); return b,None
    if form=="age_lin_w":
        w=np.sqrt(np.maximum(neff[av],1e-9)); beta,*_=np.linalg.lstsq(Xa*w[:,None],y*w,rcond=None)
    else:
        beta,*_=np.linalg.lstsq(Xa,y,rcond=None)
    return X@beta,beta

def eb_pool(bias,av,cc,neff):
    fit,_=fit_pred("age_lin",bias,av)
    sig2=np.where(av,np.maximum(cc*(1-cc),1e-4)/np.maximum(neff,1),np.nan)   # 셀평균의 표집분산(하한으로 0/0 방지)
    resid=bias-fit; tau2=max(0.0,np.nanvar(resid[av],ddof=1)-np.nanmean(sig2[av]))
    lam=np.where(av,tau2/(tau2+np.where(np.isnan(sig2),1,sig2)+1e-12),0.0)
    return np.where(av,lam*bias+(1-lam)*fit,fit)

real=Real(load_real(2024)); SYN={m:syn_cell_means(load_syn(f)) for m,f in SYN_FILES.items()}
rng=np.random.default_rng(SEED)
mae={m:{f:[] for f in FORMS} for m in SYN}; coef={m:{v:[] for v in BIN} for m in SYN}
# 민감도: 보정된 비율을 [0,1] 로 제한했을 때의 검정 MAE(주 분석은 제한하지 않는다)
mae_clip={m:{f:[] for f in FORMS} for m in SYN}
sel={m:{c:0 for c in CANDS} for m in SYN}; corrected={m:{v:[] for v in BIN} for m in SYN}
for rep in range(REPS):
    cal=stratified_split(rng,real,FRAC); tst=~cal
    inner=[stratified_split(rng,real,0.5)&cal for _ in range(INNER)]   # 보정셋 내부 재분할(마스크 교집합)
    for m,sc in SYN.items():
        acc={f:[] for f in FORMS}; accc={f:[] for f in FORMS}
        for v in BIN:
            s=sc[v]; cc=real.cell_wmean(cal,v); tc=real.cell_wmean(tst,v)
            neff=real.cell_neff(cal,v)   # 항목 결측 제외(셀평균과 동일 응답자 집합)
            av=~np.isnan(cc)&~np.isnan(s); tv=~np.isnan(tc)&~np.isnan(s); bias=s-cc
            preds={}
            for f in FORMS[:-2]:
                preds[f],beta=fit_pred(f,bias,av,neff)
                if f=="age_lin" and beta is not None: coef[m][v].append(beta)
            preds["eb_pool"]=eb_pool(bias,av,cc,neff)
            # nested: 내부 분할로 후보 선택
            score={c:[] for c in CANDS}
            for ic in inner:
                iv=cal&~ic; icc=real.cell_wmean(ic,v); ivc=real.cell_wmean(iv,v)
                iav=~np.isnan(icc)&~np.isnan(s); itv=~np.isnan(ivc)&~np.isnan(s)
                for c in CANDS:
                    p,_=fit_pred(c,s-icc,iav); score[c].append(np.mean(np.abs((s-p)-ivc)[itv]))
            best=min(CANDS,key=lambda c:np.mean(score[c])); sel[m][best]+=1
            preds["nested"]=preds[best]
            for f in FORMS:
                acc[f].append(np.mean(np.abs((s-preds[f])-tc)[tv])*100)
                accc[f].append(np.mean(np.abs(np.clip(s-preds[f],0,1)-tc)[tv])*100)
            corrected[m][v].append(s-preds["age_lin"])
        for f in FORMS:
            mae[m][f].append(np.mean(acc[f])); mae_clip[m][f].append(np.mean(accc[f]))

# ── 시트 1: 형태별 검정 MAE ──
rows=[]
for m in SYN:
    for f in FORMS:
        a=np.array(mae[m][f]); lo,hi=np.percentile(a,[2.5,97.5])
        rows.append({"모델":m,"보정형태":f,"검정MAE%p":round(a.mean(),2),"분할분위_하한":round(lo,2),"분할분위_상한":round(hi,2),
                     "검정MAE%p_클리핑[0,1]":round(np.array(mae_clip[m][f]).mean(),2)})
    tot=sum(sel[m].values())
    for c in CANDS: rows.append({"모델":m,"보정형태":f"nested 선택빈도: {c}","검정MAE%p":round(100*sel[m][c]/tot,1)})
form_df=pd.DataFrame(rows)

# ── 시트 2: age_lin 계수(분할 분포 + 전체자료 적합) + 잔차 진단 ──
full=np.ones(real.n,bool); crow=[]
for m,sc in SYN.items():
    for v in BIN:
        B=np.array(coef[m][v]); s=sc[v]; cf=real.cell_wmean(full,v); av=~np.isnan(cf)&~np.isnan(s)
        pf,bf=fit_pred("age_lin",s-cf,av); res=(s-cf-pf)[av]
        C=np.array(corrected[m][v]); hw=np.nanmean((np.nanpercentile(C,97.5,axis=0)-np.nanpercentile(C,2.5,axis=0))/2)*100
        crow.append({"모델":m,"지표":v,
            "β0(절편)_분할평균":round(B[:,0].mean()*100,2),"β0_2.5":round(np.percentile(B[:,0],2.5)*100,2),"β0_97.5":round(np.percentile(B[:,0],97.5)*100,2),
            "β1(연령밴드당pp)_분할평균":round(B[:,1].mean()*100,2),"β1_2.5":round(np.percentile(B[:,1],2.5)*100,2),"β1_97.5":round(np.percentile(B[:,1],97.5)*100,2),
            "β0_전체자료":round(bf[0]*100,2),"β1_전체자료":round(bf[1]*100,2),
            "잔차SD%p":round(res.std(ddof=1)*100,3),"최대|잔차|%p":round(np.abs(res).max()*100,2),
            "잔차-성별상관":round(np.corrcoef(res,SEXD[av])[0,1],2),
            "보정셀추정치_분할반폭%p":round(hw,3)})
coef_df=pd.DataFrame(crow)
write_sheets({"심사_보정형태민감도":form_df,"심사_보정계수":coef_df})
print(form_df.to_string(index=False)); print(coef_df.to_string(index=False))
