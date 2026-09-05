# -*- coding: utf-8 -*-
"""RQ3 보완: 실측 단독(real-only) 비교군 + 보정률 학습곡선 + 가구 단위 분할 + 셀 홀드아웃.

심사 대응 분석이다. 기존 RQ3(rq_uncertainty.py의 200분할 층화 30/70)와 동일한
프로토콜 위에서 다음을 추가로 대조한다.
  (A) 합성 무보정 / 전역 보정 / 연령회귀 보정  — 기존 3종(발표값 재현 확인용)
  (B) 실측 단독 직접추정  — 보정셋의 가중 셀평균(빈 셀은 보정셋 전체평균으로 대체)
  (C) 실측 단독 연령·성별 회귀 — 보정셋 셀평균에 대한 가중 선형회귀(연령코드+성별)
  (D) 실측 단독 전체평균  — 보정셋 가중 전체평균(설계 내 무정보 베이스라인)
설계 축: 분할 단위(개인 층화 / 가구 군집) × 보정률(1·5·10·20·30%) × 200회 반복.
추가로 셀 홀드아웃(성별×연령 셀 전체를 보정에서 제외 → 미관측 세그먼트 외삽) 검정.
난수는 전용 rng(seed 42). 결과는 워크북 3개 시트에 기록한다.
"""
import pandas as pd, numpy as np

BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CELL=["성별","연령대"]; AGES=["10대","20대","30대","40대","50대","60대","70대이상"]
ACODE={x:i for i,x in enumerate(AGES)}
FRACS=[0.01,0.05,0.10,0.20,0.30]; REPS=200; SEED=42

a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig")
a24=a[(a.YEAR==2024)&(a["연령대"].isin(AGES))].copy().reset_index(drop=True)
hid=pd.read_csv("private/PanelData_20260701.csv",encoding="utf-8-sig",usecols=["OPID","hid"]).drop_duplicates("OPID")
a24=a24.merge(hid,on="OPID",how="left")
print(f"2024 분석 표본 n={len(a24)} | hid 매칭 {a24['hid'].notna().mean()*100:.1f}% | 가구 {a24['hid'].nunique()}")

# ── 벡터화 준비: 셀 정수코드·지표 배열 ──────────────────────────────
cells=[(s,g) for s in ["남성","여성"] for g in AGES]           # 14셀 고정 순서
cidx={c:i for i,c in enumerate(cells)}; NC=len(cells)
cell_of=a24.apply(lambda r:cidx[(r["성별"],r["연령대"])],axis=1).to_numpy()
wt=a24["WT"].to_numpy(float)
sexd=np.array([1.0 if c[0]=="여성" else 0.0 for c in cells])   # 셀별 성별 더미
agec=np.array([float(ACODE[c[1]]) for c in cells])             # 셀별 연령코드
Y={v:a24[v].to_numpy(float) for v in BIN}

def cell_wmean(mask,v):
    """mask 부분표본의 가중 셀평균(14,). 자료 없는 셀은 nan."""
    y=Y[v]; ok=mask&~np.isnan(y)
    num=np.bincount(cell_of[ok],weights=(y*wt)[ok],minlength=NC)
    den=np.bincount(cell_of[ok],weights=wt[ok],minlength=NC)
    with np.errstate(invalid="ignore"):
        return np.where(den>0,num/den,np.nan)

def grand_wmean(mask,v):
    y=Y[v]; ok=mask&~np.isnan(y)
    return np.average(y[ok],weights=wt[ok]) if ok.any() else np.nan

def fit_bias_reg(bias,avail):
    """합성-실측 편향의 연령 선형적합(기존 프로토콜과 동일: 연령코드 단변량)."""
    if avail.sum()>=3:
        sl,ic=np.polyfit(agec[avail],bias[avail],1)
        return sl*agec+ic
    return np.full(NC,np.nanmean(bias[avail]) if avail.any() else 0.0)

def fit_rate_reg(rate,wcell,avail):
    """실측 단독: 보정셋 셀평균 rate ~ 연령코드+성별 가중 선형회귀 → 전 셀 예측([0,1] 절단)."""
    if avail.sum()>=3:
        X=np.column_stack([np.ones(avail.sum()),agec[avail],sexd[avail]])
        W=np.sqrt(np.maximum(wcell[avail],1e-9))
        beta,*_=np.linalg.lstsq(X*W[:,None],rate[avail]*W,rcond=None)
        pred=beta[0]+beta[1]*agec+beta[2]*sexd
        return np.clip(pred,0,1)
    return np.full(NC,np.nanmean(rate[avail]) if avail.any() else np.nan)

# 합성 셀평균(분할 불변) 사전계산
SYN={}
for m,f in [("Gemini","outputs/synthetic_recoded_gemini.csv"),("EXAONE","outputs/synthetic_recoded_exaone.csv")]:
    s=pd.read_csv(f,encoding="utf-8-sig")
    sc={}
    for v in BIN:
        g=s.groupby(CELL)[v].mean()
        sc[v]=np.array([g.get(c,np.nan) for c in cells])
    SYN[m]=sc

hh_ids=a24["hid"].to_numpy()
uniq_hh=pd.unique(hh_ids)

def make_split(rng,frac,mode):
    """보정셋 마스크 생성. individual=셀 내 층화, household=가구 군집(비층화)."""
    m=np.zeros(len(a24),bool)
    if mode=="individual":
        for ci in range(NC):
            idx=np.where(cell_of==ci)[0]; rng.shuffle(idx)
            m[idx[:int(len(idx)*frac)]]=True
    else:
        hh=uniq_hh.copy(); rng.shuffle(hh)
        m=np.isin(hh_ids,hh[:int(len(hh)*frac)])
    return m

# ── 1) 학습곡선: 분할모드 × 보정률 × 200회 ──────────────────────────
rows=[]; paired={}
for mode in ["individual","household"]:
    rng=np.random.default_rng(SEED)
    for frac in FRACS:
        acc={m:{k:[] for k in ["syn_unc","syn_glob","syn_reg","real_dir","real_reg","real_gm"]} for m in SYN}
        fb_cnt=0
        for _ in range(REPS):
            cal=make_split(rng,frac,mode); tst=~cal
            for m,sc in SYN.items():
                e={k:[] for k in acc[m]}
                for v in BIN:
                    cc=cell_wmean(cal,v); tc=cell_wmean(tst,v); gm=grand_wmean(cal,v)
                    tv=~np.isnan(tc)                       # 평가 셀
                    av=tv&~np.isnan(cc)                    # 보정 학습 가능 셀
                    s=sc[v]
                    bias=s-cc
                    b=np.nanmean(bias[av]) if av.any() else 0.0
                    pred_b=fit_bias_reg(bias,av&~np.isnan(s))
                    rreg=fit_rate_reg(cc,np.bincount(cell_of[cal&~np.isnan(Y[v])],weights=wt[cal&~np.isnan(Y[v])],minlength=NC),av)   # 문항 응답자 기준 회귀 가중
                    rdir=np.where(np.isnan(cc),gm,cc)      # 빈 셀은 보정셋 전체평균 대체
                    fb_cnt+=int(np.isnan(cc[tv]).sum())
                    e["syn_unc"]+=list(np.abs(s-tc)[tv&~np.isnan(s)])
                    e["syn_glob"]+=list(np.abs((s-b)-tc)[tv&~np.isnan(s)])
                    e["syn_reg"]+=list(np.abs((s-pred_b)-tc)[tv&~np.isnan(s)])
                    e["real_dir"]+=list(np.abs(rdir-tc)[tv])
                    e["real_reg"]+=list(np.abs(rreg-tc)[tv])
                    e["real_gm"]+=list(np.abs(gm-tc)[tv])
                for k in acc[m]: acc[m][k].append(np.mean(e[k])*100)
        for m in SYN:
            r={"분할":mode,"보정률":frac,"모델":m}
            for k in acc[m]: r[k+"_MAE%p"]=round(np.mean(acc[m][k]),1)
            d=np.array(acc[m]["syn_reg"])-np.array(acc[m]["real_dir"])
            lo,hi=np.percentile(d,[2.5,97.5])
            r["차이_synreg-realdir%p"]=round(np.mean(d),1); r["차이_CI"]=f"[{lo:.1f}, {hi:.1f}]"
            rows.append(r)
            if mode=="individual" and frac==0.30: paired[m]=(np.mean(d),lo,hi)
        print(f"[{mode} f={frac:.2f}] "+" | ".join(
            f"{m}: 무보정 {rows[-2+i]['syn_unc_MAE%p']} 연령회귀 {rows[-2+i]['syn_reg_MAE%p']} "
            f"실측직접 {rows[-2+i]['real_dir_MAE%p']} 실측회귀 {rows[-2+i]['real_reg_MAE%p']} "
            f"실측전체평균 {rows[-2+i]['real_gm_MAE%p']}" for i,m in enumerate(SYN)))

lc=pd.DataFrame(rows)

# ── 2) 셀 홀드아웃: 셀 전체를 보정에서 제외 → 외삽 검정 ──────────────
rng=np.random.default_rng(SEED); HREPS=50
hrows=[]
full_c={v:cell_wmean(np.ones(len(a24),bool),v) for v in BIN}   # 평가 목표: 전체 실측 셀평균
for m,sc in SYN.items():
    e={k:[] for k in ["syn_unc","syn_glob","syn_reg","real_reg","real_gm"]}
    for j in range(NC):
        others=cell_of!=j
        for _ in range(HREPS):
            cal=np.zeros(len(a24),bool)
            for ci in range(NC):
                if ci==j: continue
                idx=np.where(cell_of==ci)[0]; rng.shuffle(idx)
                cal[idx[:int(len(idx)*0.30)]]=True
            for v in BIN:
                t=full_c[v][j]
                if np.isnan(t) or np.isnan(sc[v][j]): continue
                cc=cell_wmean(cal,v); gm=grand_wmean(cal,v)
                av=~np.isnan(cc); av[j]=False
                bias=sc[v]-cc
                b=np.nanmean(bias[av]) if av.any() else 0.0
                pred_b=fit_bias_reg(bias,av&~np.isnan(sc[v]))
                rreg=fit_rate_reg(cc,np.bincount(cell_of[cal&~np.isnan(Y[v])],weights=wt[cal&~np.isnan(Y[v])],minlength=NC),av)   # 문항 응답자 기준 회귀 가중
                e["syn_unc"].append(abs(sc[v][j]-t))
                e["syn_glob"].append(abs((sc[v][j]-b)-t))
                e["syn_reg"].append(abs((sc[v][j]-pred_b[j])-t))
                e["real_reg"].append(abs(rreg[j]-t))
                e["real_gm"].append(abs(gm-t))
    hrows.append({"모델":m,**{k+"_MAE%p":round(np.mean(v)*100,1) for k,v in e.items()},
                  "설계":f"14셀 각 전체 홀드아웃×{HREPS}회, 나머지 13셀의 30% 보정"})
ho=pd.DataFrame(hrows)

# ── 기록·출력 ────────────────────────────────────────────────────────
with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    lc.to_excel(w,sheet_name="RQ3_실측단독_학습곡선",index=False)
    ho.to_excel(w,sheet_name="RQ3_셀홀드아웃",index=False)
print("\n워크북 시트 추가: RQ3_실측단독_학습곡선 / RQ3_셀홀드아웃")
print("\n=== 30% 개인층화(발표 프로토콜)에서 합성보정−실측직접 차이(양수=실측이 우월) ===")
for m,(d,lo,hi) in paired.items(): print(f"  {m}: {d:+.1f}%p [95% 분할분위 {lo:.1f}, {hi:.1f}]")
print("\n=== 셀 홀드아웃(미관측 세그먼트 외삽) ===")
print(ho.to_string(index=False))
