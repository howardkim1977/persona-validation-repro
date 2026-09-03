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
                      "설계":"2024 학습 → 2025 검정","비고":"Table 7 bottom and caption(시점 홀드아웃, out-of-time 베이스라인 대비)"})
with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    pd.DataFrame(temp_rows).to_excel(w,sheet_name="RQ3_시점홀드아웃",index=False)
print("워크북 시트 추가: RQ3_시점홀드아웃")

print("\n"+"="*66)
print("m8. 자명 베이스라인 대비 (세그먼트 셀 MAE %p, 2024)")
print("="*66)
# 베이스라인1: 전체 평균(주변분포) — 세그먼트 정보 없음
# 베이스라인2: 전차수(2023) 실측 셀평균 — 과거 실측 사용
a23=a[a.YEAR==2023]
# 비교 셀은 논문과 같이 14개 성별×연령대 셀(10세 미만 제외)로 제한하고, 전체평균 베이스라인도
# 같은 10세 이상 표본의 가중 전체 비율로 계산한다(논문 Table 9: 11.6 / 11.1 / 3.7).
a24r=a24[a24["연령대"].isin(AGES)]
COMMON6=[v for v in BIN if v in a23.columns and a23[v].notna().any()]   # 2023 차수에 실측이 있는 6개 지표
def cell_err(items,syn=None):
    """14셀 기준 셀 MAE(%p): 합성(syn), 전체평균 베이스라인, 전차수(2023) 베이스라인."""
    syn_e=[];gm_e=[];prev_e=[]
    for v in items:
        ac=cwm_w(a24,v); pc=cwm_w(a23,v) if v in a23.columns else {}
        s=a24r[[v,"WT"]].dropna(); grand=np.average(s[v],weights=s["WT"])
        cells=[k for k in ac if k[1] in AGES and not np.isnan(ac[k])]
        if syn is not None:
            sc=cwm(syn,v); syn_e+=[abs(sc[k]-ac[k]) for k in cells if k in sc]
        gm_e+=[abs(grand-ac[k]) for k in cells]
        prev_e+=[abs(pc[k]-ac[k]) for k in cells if k in pc and not np.isnan(pc[k])]
    f=lambda x: round(np.mean(x)*100,1) if x else np.nan
    return f(syn_e),f(gm_e),f(prev_e)
base_rows=[]
for m,f in [("Gemini","outputs/synthetic_recoded_gemini.csv"),("EXAONE","outputs/synthetic_recoded_exaone.csv")]:
    syn=pd.read_csv(f,encoding="utf-8-sig")
    s6,_,_=cell_err(COMMON6,syn); s8,_,_=cell_err(BIN,syn)
    base_rows.append({"조건":f"무보정 합성 {m}","공통6_셀MAE":s6,"전체8_셀MAE":s8})
    print(f"  {m}: 합성 공통6 {s6} / 전체8 {s8}")
_,g6,p6=cell_err(COMMON6); _,g8,_=cell_err(BIN)
base_rows.append({"조건":"전체평균 베이스라인","공통6_셀MAE":g6,"전체8_셀MAE":g8})
base_rows.append({"조건":"전차수(2023) 베이스라인","공통6_셀MAE":p6,"전체8_셀MAE":np.nan})
print(f"  전체평균 베이스라인 공통6 {g6} / 전체8 {g8} | 전차수(2023) 공통6 {p6}  (14셀 기준; 공통6 = {COMMON6})")
with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    pd.DataFrame(base_rows).to_excel(w,sheet_name="베이스라인_공통6",index=False)
print("워크북 시트 갱신: 베이스라인_공통6 (14셀)")
