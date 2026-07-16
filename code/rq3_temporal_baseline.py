# -*- coding: utf-8 -*-
"""M3: 시점 홀드아웃 보정(2024 학습 → 2025 검정) + m8: 자명 베이스라인 대비."""
import pandas as pd, numpy as np
BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CELL=["성별","연령대"]; AGES=["10대","20대","30대","40대","50대","60대","70대이상"]
AC={x:i for i,x in enumerate(AGES)}
a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig")
a24=a[a.YEAR==2024]; a25=a[a.YEAR==2025]
def cwm_w(df,v):
    o={}
    for k,s in df.groupby(CELL):
        t=s[[v,"WT"]].dropna(); o[k]=np.average(t[v],weights=t["WT"]) if len(t) else np.nan
    return o
def cwm(df,v): return {k:s[v].mean() for k,s in df.groupby(CELL)}

print("="*66)
print("M3. 시점 홀드아웃: 2024로 보정 학습 → 2025로 검정 (셀 MAE %p)")
print("="*66)
temp_rows=[]
for m,f24,f25 in [("Gemini","outputs/synthetic_recoded_gemini.csv","outputs/synthetic_recoded_2025_gemini.csv"),
                  ("EXAONE","outputs/synthetic_recoded_exaone.csv","outputs/synthetic_recoded_2025_exaone.csv")]:
    s24=pd.read_csv(f24,encoding="utf-8-sig"); s25=pd.read_csv(f25,encoding="utf-8-sig")
    unc=[];glob=[];reg=[];gm=[];prev=[]
    for v in BIN:
        sc24=cwm(s24,v); ac24=cwm_w(a24,v); sc25=cwm(s25,v); ac25=cwm_w(a25,v)
        cells=[k for k in sc25 if k in ac25 and not np.isnan(ac25[k])]
        # 2024에서 편향 학습
        bcells=[k for k in sc24 if k in ac24 and not np.isnan(ac24[k])]
        b=np.mean([sc24[k]-ac24[k] for k in bcells])           # 전역
        xs=[(AC[k[1]],sc24[k]-ac24[k]) for k in bcells if k[1] in AC]
        sl,ic=np.polyfit([x for x,_ in xs],[y for _,y in xs],1) if len(xs)>=3 else (0,b)
        # 시점 밖(out-of-time) 자명 베이스라인: 2025 전체평균, 전차수(2024) 셀평균
        t25=a25[[v,"WT"]].dropna(); g25=np.average(t25[v],weights=t25["WT"]) if len(t25) else np.nan
        unc+=[abs(sc25[k]-ac25[k]) for k in cells]
        glob+=[abs((sc25[k]-b)-ac25[k]) for k in cells]
        reg+=[abs((sc25[k]-(sl*AC[k[1]]+ic))-ac25[k]) for k in cells if k[1] in AC]
        gm+=[abs(g25-ac25[k]) for k in cells]
        prev+=[abs(ac24[k]-ac25[k]) for k in cells if k in ac24 and not np.isnan(ac24[k])]
    print(f"  {m}: 무보정 {np.mean(unc)*100:.1f} / 전역(2024학습) {np.mean(glob)*100:.1f} / "
          f"연령회귀(2024학습) {np.mean(reg)*100:.1f} / [베이스라인] 전체평균(2025) {np.mean(gm)*100:.1f} / 전차수(2024) {np.mean(prev)*100:.1f}")
    temp_rows.append({"모델":m,"무보정_MAE%p":round(np.mean(unc)*100,1),
                      "전역보정_MAE%p":round(np.mean(glob)*100,1),
                      "연령회귀_MAE%p":round(np.mean(reg)*100,1),
                      "전체평균BL_2025_MAE%p":round(np.mean(gm)*100,1),
                      "전차수BL_2024_MAE%p":round(np.mean(prev)*100,1),
                      "설계":"2024 학습 → 2025 검정","비고":"본문 Table 3 하단+캡션(시점 홀드아웃, out-of-time 베이스라인 대비)"})
with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    pd.DataFrame(temp_rows).to_excel(w,sheet_name="RQ3_시점홀드아웃",index=False)
print("워크북 시트 추가: RQ3_시점홀드아웃")

print("\n"+"="*66)
print("m8. 자명 베이스라인 대비 (세그먼트 셀 MAE %p, 2024)")
print("="*66)
# 베이스라인1: 전체 평균(주변분포) — 세그먼트 정보 없음
# 베이스라인2: 전차수(2023) 실측 셀평균 — 과거 실측 사용
a23=a[a.YEAR==2023]
for m,f in [("Gemini","outputs/synthetic_recoded_gemini.csv"),("EXAONE","outputs/synthetic_recoded_exaone.csv")]:
    syn=pd.read_csv(f,encoding="utf-8-sig")
    syn_e=[];gm_e=[];prev_e=[]
    for v in BIN:
        ac=cwm_w(a24,v); sc=cwm(syn,v)
        s=a24[[v,"WT"]].dropna(); grand=np.average(s[v],weights=s["WT"])
        pc=cwm_w(a23,v) if v in a23 else {}
        cells=[k for k in ac if not np.isnan(ac[k])]
        syn_e+=[abs(sc[k]-ac[k]) for k in cells if k in sc]
        gm_e+=[abs(grand-ac[k]) for k in cells]
        prev_e+=[abs(pc[k]-ac[k]) for k in cells if k in pc and not np.isnan(pc[k])]
    print(f"  {m}: 합성 {np.mean(syn_e)*100:.1f} | 전체평균 베이스라인 {np.mean(gm_e)*100:.1f} | "
          f"전차수(2023)실측 {np.mean(prev_e)*100:.1f}")
