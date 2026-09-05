# -*- coding: utf-8 -*-
"""불확실성 정량화(부트스트랩 CI) + 정확한 표본수 집계."""
import pandas as pd, numpy as np
BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CELL=["성별","연령대"]; AGES=["10대","20대","30대","40대","50대","60대","70대이상"]
ACODE={x:i for i,x in enumerate(AGES)}
rng=np.random.default_rng(42)
a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig")

# ── 정확한 표본수 ──
print("=== 표본수 ===")
for yr in [2024,2025]:
    print(f"실측 {yr}: n={int((a.YEAR==yr).sum())}")
for lbl,f in [("Gemini2024","outputs/synthetic_responses.csv"),("EXAONE2024","outputs/synthetic_exaone.csv"),
              ("Gemini2025","outputs/synthetic_2025.csv"),("EXAONE2025","outputs/synthetic_exaone_2025.csv")]:
    d=pd.read_csv(f,encoding="utf-8-sig"); err=int(d["_error"].notna().sum()) if "_error" in d else 0
    print(f"합성 {lbl}: 생성 {len(d)}, 유효 {len(d)-err}")

# ── RQ1 MAE 부트스트랩(2024) ──
def cwm_s(df,v): return {k:df.loc[df.index.isin(idx),v].mean() for k,idx in df.groupby(CELL).groups.items()}
def rq1_mae(act,syn):
    scell={v:{k:s[v].mean() for k,s in syn.groupby(CELL)} for v in BIN}
    errs=[]
    for v in BIN:
        s=act[[v,"WT"]].dropna(); actm=np.average(s[v],weights=s["WT"])
        # 조건부 문항은 그 문항 응답자만으로 셀 점유율을 계산한다
        cw=act[act[v].notna()].groupby(CELL)["WT"].sum(); share=(cw/cw.sum()).to_dict()
        cm=scell[v]; num=sum(share.get(k,0)*cm[k] for k in cm if k in share and not np.isnan(cm[k]))
        den=sum(share.get(k,0) for k in cm if k in share and not np.isnan(cm[k]))
        errs.append(abs(num/den-actm))
    return np.mean(errs)*100

a24=a[a.YEAR==2024]
print("\n=== RQ1 MAE 95% CI (부트스트랩 B=600, 2024) ===")
for m,f in [("Gemini","outputs/synthetic_recoded_gemini.csv"),("EXAONE","outputs/synthetic_recoded_exaone.csv")]:
    syn=pd.read_csv(f,encoding="utf-8-sig")
    pt=rq1_mae(a24,syn); boot=[]
    for _ in range(600):
        ab=a24.sample(len(a24),replace=True,random_state=rng.integers(1e9))
        sb=syn.sample(len(syn),replace=True,random_state=rng.integers(1e9))
        boot.append(rq1_mae(ab,sb))
    lo,hi=np.percentile(boot,[2.5,97.5])
    print(f"  {m}: MAE {pt:.1f}%p [95% CI {lo:.1f}, {hi:.1f}]")

# ── RQ3 개선폭 반복분할 CI ──
# 분할 난수는 전용 rng(seed 42)를 사용한다. RQ1 부트스트랩 난수열과 분리해
# 이 절만 단독 실행해도 동일 결과가 재현되도록 한다(Table 7 채택 추정치).
rng=np.random.default_rng(42)
print("\n=== RQ3 보정 개선폭 (반복 홀드아웃 200회, 검정셋 MAE) ===")
def cwm_w(df,v):
    o={}
    for k,s in df.groupby(CELL):
        t=s[[v,"WT"]].dropna(); o[k]=np.average(t[v],weights=t["WT"]) if len(t) else np.nan
    return o
def cwm(df,v): return {k:s[v].mean() for k,s in df.groupby(CELL)}
rows=[]
for m,f in [("Gemini","outputs/synthetic_recoded_gemini.csv"),("EXAONE","outputs/synthetic_recoded_exaone.csv")]:
    syn=pd.read_csv(f,encoding="utf-8-sig")
    unc=[];glo=[];reg=[]
    for _ in range(200):
        a24=a24.copy(); a24["_c"]=False
        for _,idx in a24.groupby(CELL).groups.items():
            idx=list(idx); rng.shuffle(idx); a24.loc[idx[:int(len(idx)*0.3)],"_c"]=True
        cal=a24[a24._c]; tst=a24[~a24._c]
        u=[];g=[];r=[]
        for v in BIN:
            sc=cwm(syn,v); cc=cwm_w(cal,v); tc=cwm_w(tst,v)
            cells=[k for k in sc if k in tc and not np.isnan(tc[k])]
            u+=[abs(sc[k]-tc[k]) for k in cells]
            bs=[sc[k]-cc[k] for k in cc if k in sc and not np.isnan(cc[k])]
            if bs:
                b=np.mean(bs); g+=[abs((sc[k]-b)-tc[k]) for k in cells]
            xs=[(ACODE[k[1]],sc[k]-cc[k]) for k in cc if k in sc and not np.isnan(cc[k]) and k[1] in ACODE]
            if len(xs)>=3:
                X=np.array([x for x,_ in xs]);Y=np.array([y for _,y in xs]);sl,ic=np.polyfit(X,Y,1)
                r+=[abs((sc[k]-(sl*ACODE[k[1]]+ic))-tc[k]) for k in cells]
        unc.append(np.mean(u)*100); glo.append(np.mean(g)*100); reg.append(np.mean(r)*100)
    imp=np.array(unc)-np.array(reg)
    lo,hi=np.percentile(imp,[2.5,97.5])
    print(f"  {m}: 무보정 {np.mean(unc):.1f} / 전역 {np.mean(glo):.1f} / 연령회귀 {np.mean(reg):.1f} / "
          f"개선 {np.mean(imp):.1f}%p [95% CI {lo:.1f}, {hi:.1f}]")
    rows.append({"모델":m,"무보정_MAE%p":round(np.mean(unc),1),"전역보정_MAE%p":round(np.mean(glo),1),
                 "연령회귀_MAE%p":round(np.mean(reg),1),"개선_연령회귀%p":round(np.mean(imp),1),
                 "개선_95CI_하한":round(lo,1),"개선_95CI_상한":round(hi,1),
                 "분할":"층화 30/70 반복 200회","비고":"Table 7 top(채택 추정치)"})

with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    pd.DataFrame(rows).to_excel(w,sheet_name="RQ3_보정",index=False)
print("\n워크북 시트 갱신: RQ3_보정(200분할 평균·CI)")
