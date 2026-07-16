# -*- coding: utf-8 -*-
"""RQ3 보정: 홀드아웃 설계.
실측 2024를 보정셋(30%)/검정셋(70%)로 층화분할. 보정셋으로 합성의 셀별 편향을
학습해 합성 셀레이트를 교정하고, 검정셋(가중) 대비 보정 전후 예측오차(MAE) 비교.
보정법 3종: (0)무보정 (1)전역 가산편향 (2)인구통계(연령·성별) 회귀편향."""
import pandas as pd, numpy as np
BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CELL=["성별","연령대"]; AGES=["10대","20대","30대","40대","50대","60대","70대이상"]
ACODE={x:i for i,x in enumerate(AGES)}
a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig"); a24=a[a.YEAR==2024].copy()
rng=np.random.default_rng(42)
# 층화 분할(셀 내 무작위 30/70)
a24["_calib"]=False
for _,idx in a24.groupby(CELL).groups.items():
    idx=list(idx); rng.shuffle(idx); k=int(len(idx)*0.3)
    a24.loc[idx[:k],"_calib"]=True
calib=a24[a24._calib]; test=a24[~a24._calib]
def cwm_w(df,v):
    o={}
    for k,s in df.groupby(CELL):
        t=s[[v,"WT"]].dropna(); o[k]=np.average(t[v],weights=t["WT"]) if len(t) else np.nan
    return o
def cwm_s(df,v): return {k:s[v].mean() for k,s in df.groupby(CELL)}

results=[]
for m,f in [("Gemini","outputs/synthetic_recoded_gemini.csv"),("EXAONE","outputs/synthetic_recoded_exaone.csv")]:
    syn=pd.read_csv(f,encoding="utf-8-sig")
    pre=[];g_post=[];r_post=[]
    for v in BIN:
        s_cell=cwm_s(syn,v); c_cell=cwm_w(calib,v); t_cell=cwm_w(test,v)
        cells=[k for k in s_cell if k in t_cell and not np.isnan(t_cell[k])]
        # (0) 무보정: 합성 vs 검정
        pre+=[abs(s_cell[k]-t_cell[k]) for k in cells]
        # (1) 전역 가산편향: b=mean(합성-보정), 교정=합성-b
        cb=[s_cell[k]-c_cell[k] for k in c_cell if k in s_cell and not np.isnan(c_cell[k])]
        b=np.mean(cb)
        g_post+=[abs((s_cell[k]-b)-t_cell[k]) for k in cells]
        # (2) 연령회귀 편향: 보정셋에서 bias~연령코드 선형적합 → 전 셀 예측 편향 차감
        xs=[];ys=[]
        for k in c_cell:
            if k in s_cell and not np.isnan(c_cell[k]):
                xs.append(ACODE.get(k[1],np.nan)); ys.append(s_cell[k]-c_cell[k])
        xs2=[(x,y) for x,y in zip(xs,ys) if not np.isnan(x)]
        if len(xs2)>=3:
            X=np.array([x for x,_ in xs2]); Y=np.array([y for _,y in xs2])
            sl,ic=np.polyfit(X,Y,1)
            pred=lambda k:sl*ACODE.get(k[1],np.nan)+ic
        else:
            pred=lambda k:b
        r_post+=[abs((s_cell[k]-pred(k))-t_cell[k]) for k in cells]
    results.append({"모델":m,
        "무보정MAE%p":round(np.mean(pre)*100,1),
        "전역보정MAE%p":round(np.mean(g_post)*100,1),
        "연령회귀보정MAE%p":round(np.mean(r_post)*100,1)})
res=pd.DataFrame(results)
res["전역_개선%p"]=res["무보정MAE%p"]-res["전역보정MAE%p"]
res["연령회귀_개선%p"]=res["무보정MAE%p"]-res["연령회귀보정MAE%p"]
with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    res.to_excel(w,sheet_name="RQ3_보정_단일분할",index=False)
print("워크북 시트 추가: RQ3_보정_단일분할 (채택 추정치는 rq_uncertainty.py의 RQ3_보정 200분할 평균)")
print(f"보정셋 n={len(calib)} / 검정셋 n={len(test)}\n")
print(res.to_string(index=False))
