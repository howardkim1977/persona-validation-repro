# -*- coding: utf-8 -*-
"""R2-9 분석: 문항 제시 순서 무작위화 실험(order_experiment.py 산출물).
동일 페르소나 부분표본(n≈1,144)에서
  F1·F2·F3 = 고정(코드북) 순서 3회 독립 응답, R1 = 페르소나별 무작위 순서 1회.
보고:
  (1) 지표별 사후층화 이용률: F1 vs R1(순서 효과), F1 vs F2(생성 노이즈 귀무 기준)
  (2) 페르소나 짝지음 불일치율(같은 페르소나가 F1과 R1에서 다른 답을 낸 비율) vs F1–F2 불일치율
  (3) 2024 기준 추정치 대비 MAE: F1, F2, F3, R1, 그리고 F1~F3 평균
  (4) 구성개념 평균 F1 vs R1
  (5) Gemini 계층 부트스트랩(가구→페르소나→3응답 중 1개) — 부분표본
부트스트랩 CI 는 페르소나 단위 재표집(B=2000, seed 42)."""
import json, numpy as np, pandas as pd
from rr_common import *
from recode import recode

B=2000; rng=np.random.default_rng(SEED)
def load_arm(arm):
    d=pd.read_csv(f"outputs/order_exp_gemini_{arm}.csv",encoding="utf-8-sig")
    if "_error" in d: d=d[d["_error"].isna()]
    r=recode(d); r["_idx"]=d["_idx"].values; r=r[r["연령대"].isin(AGES)]
    r["_cell"]=[CIDX[(g,a)] for g,a in zip(r["성별"],r["연령대"])]; return r.set_index("_idx")
A={arm:load_arm(arm) for arm in ["F1","F2","F3","R1"]}
common=sorted(set.intersection(*[set(v.index) for v in A.values()])); n=len(common)
print(f"4개 암 공통 유효 페르소나 {n} (F1 {len(A['F1'])}, F2 {len(A['F2'])}, F3 {len(A['F3'])}, R1 {len(A['R1'])})")
real=Real(load_real(2024)); share=real.cell_share(); RR={v:real.overall_wmean(v) for v in BIN}
cell=A["F1"].loc[common,"_cell"].to_numpy()
Y={arm:{v:A[arm].loc[common,v].to_numpy(float) for v in BIN} for arm in A}
C={arm:{v:A[arm].loc[common,v].to_numpy(float) for v in CON} for arm in A}

def ps_rate(y,idx):
    c=cell[idx]; yy=y[idx]; ok=~np.isnan(yy)
    num=np.bincount(c[ok],weights=yy[ok],minlength=NC); den=np.bincount(c[ok],minlength=NC)
    with np.errstate(invalid="ignore"): cm=np.where(den>0,num/den,np.nan)
    return post_stratified_rate(share,cm)
full=np.arange(n)
rows=[]; pv=[]
for v in BIN:
    f1=ps_rate(Y["F1"][v],full); f2=ps_rate(Y["F2"][v],full); r1=ps_rate(Y["R1"][v],full)
    dFR=[]; dFF=[]
    for _ in range(B):
        idx=rng.integers(0,n,n); dFR.append(ps_rate(Y["R1"][v],idx)-ps_rate(Y["F1"][v],idx)); dFF.append(ps_rate(Y["F2"][v],idx)-ps_rate(Y["F1"][v],idx))
    dFR=np.array(dFR)*100; dFF=np.array(dFF)*100
    p=max(2*min((dFR<=0).mean(),(dFR>=0).mean()),1/B); pv.append(p)
    a1=Y["F1"][v]; a2=Y["R1"][v]; a3=Y["F2"][v]; ok=~np.isnan(a1)&~np.isnan(a2)&~np.isnan(a3)
    rows.append({"지표":v,"실측2024%":round(RR[v]*100,1),"F1%":round(f1*100,1),"F2%":round(f2*100,1),"R1%":round(r1*100,1),
                 "Δ(R1−F1)%p":round((r1-f1)*100,1),"Δ_CI":f"[{np.percentile(dFR,2.5):.1f}, {np.percentile(dFR,97.5):.1f}]","부트스트랩p":round(p,4),
                 "Δ(F2−F1)%p":round((f2-f1)*100,1),"ΔFF_CI":f"[{np.percentile(dFF,2.5):.1f}, {np.percentile(dFF,97.5):.1f}]",
                 "불일치율_F1vsR1%":round(100*np.mean(a1[ok]!=a2[ok]),1),"불일치율_F1vsF2%":round(100*np.mean(a1[ok]!=a3[ok]),1)})
hp=holm(pv)
for r,h in zip(rows,hp): r["Holm_p"]=round(h,4)
tab=pd.DataFrame(rows); print(tab.to_string(index=False))

# MAE vs 2024 기준(부분표본, 사후층화)
mae={}
for arm in ["F1","F2","F3","R1"]:
    mae[arm]=np.mean([abs(ps_rate(Y[arm][v],full)-RR[v]) for v in BIN])*100
Yavg={v:np.nanmean(np.stack([Y[a][v] for a in ["F1","F2","F3"]]),axis=0) for v in BIN}
mae["F평균(3회)"]=np.mean([abs(ps_rate(Yavg[v],full)-RR[v]) for v in BIN])*100
mae_rows=[{"암":k,"RQ1_MAE%p(부분표본)":round(v,2)} for k,v in mae.items()]
print("\nMAE vs 2024:", {k:round(v,2) for k,v in mae.items()})

# 구성개념 평균
con_rows=[]
for v in CON:
    f1=np.nanmean(C["F1"][v]); r1=np.nanmean(C["R1"][v]); f2=np.nanmean(C["F2"][v])
    con_rows.append({"구성개념":v,"F1":round(f1,3),"F2":round(f2,3),"R1":round(r1,3),"Δ(R1−F1)":round(r1-f1,3),"Δ(F2−F1)":round(f2-f1,3)})
con=pd.DataFrame(con_rows); print(con.to_string(index=False))

# Gemini 계층 부트스트랩(가구→페르소나→3응답 중 1개), 부분표본
Ystack=np.stack([np.stack([Y[a][v] for v in BIN],axis=1) for a in ["F1","F2","F3"]])   # (3,n,8)
def mae_from(idx_r,ymat,idx_p):
    w=real.wt[idx_r]; c=real.cell[idx_r]; sh=np.bincount(c,weights=w,minlength=NC); sh=sh/sh.sum(); errs=[]
    for j,v in enumerate(BIN):
        yr=real.Y[v][idx_r]; ok=~np.isnan(yr); ar=np.average(yr[ok],weights=w[ok])
        ys=ymat[idx_p,j]; cs=cell[idx_p]; ok2=~np.isnan(ys)
        num=np.bincount(cs[ok2],weights=ys[ok2],minlength=NC); den=np.bincount(cs[ok2],minlength=NC)
        with np.errstate(invalid="ignore"): cm=np.where(den>0,num/den,np.nan)
        errs.append(abs(post_stratified_rate(sh,cm)-ar))
    return np.mean(errs)*100
rng2=np.random.default_rng(SEED); res={"단일패스(F1)":[],"계층(페르소나×3응답)":[],"페르소나재표집_3응답평균":[]}
for _ in range(600):
    ir=household_resample_index(rng2,real); ip=rng2.integers(0,n,n)
    res["단일패스(F1)"].append(mae_from(ir,Ystack[0],ip))
    pick=rng2.integers(0,3,n); res["계층(페르소나×3응답)"].append(mae_from(ir,Ystack[pick,ip,:],np.arange(n)))
    res["페르소나재표집_3응답평균"].append(mae_from(ir,np.nanmean(Ystack,axis=0),ip))
hb=[{"설계":k,"CI_하한":round(np.percentile(v,2.5),2),"CI_상한":round(np.percentile(v,97.5),2),"CI폭":round(np.percentile(v,97.5)-np.percentile(v,2.5),2)} for k,v in res.items()]
print(pd.DataFrame(hb).to_string(index=False))
write_sheets({"심사_순서실험_지표":tab,"심사_순서실험_MAE":pd.DataFrame(mae_rows),"심사_순서실험_구성개념":con,"심사_계층부트스트랩_Gemini":pd.DataFrame(hb)})
