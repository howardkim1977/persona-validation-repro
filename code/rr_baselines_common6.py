# -*- coding: utf-8 -*-
"""Table 9 보조값: 2023 차수에도 있는 공통 6개 지표에 대한 선형 연령 보정(post-hoc, 발표 형태)의
200회 층화 30/70 홀드아웃 셀 MAE(14셀, 10세 이상). 전체 8개 지표 값(≈8.6/6.7)도 함께 출력한다.
패키지 루트에서 실행: python code/rr_baselines_common6.py (analysis_ready.csv 필요)."""
import numpy as np, pandas as pd
from rr_common import *
COMMON6=["OTT_이용","유튜브_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
REPS=200; FRAC=0.30
real=Real(load_real(2024,with_hid=False)); SYN={m:syn_cell_means(load_syn(f)) for m,f in SYN_FILES.items()}
rng=np.random.default_rng(SEED); rows=[]
err={m:{v:[] for v in BIN} for m in SYN}
for _ in range(REPS):
    cal=stratified_split(rng,real,FRAC); tst=~cal
    for m,sc in SYN.items():
        for v in BIN:
            c=real.cell_wmean(cal,v); t=real.cell_wmean(tst,v); s=sc[v]
            av=~np.isnan(c)&~np.isnan(s); bias=s-c
            X=np.column_stack([np.ones(av.sum()),AGEC[av]]); beta,*_=np.linalg.lstsq(X,bias[av],rcond=None)
            corr=s-(beta[0]+beta[1]*AGEC); ok=~np.isnan(t)&~np.isnan(corr)
            err[m][v].append(np.mean(np.abs(corr[ok]-t[ok]))*100)
for m in SYN:
    e6=np.mean([np.mean(err[m][v]) for v in COMMON6]); e8=np.mean([np.mean(err[m][v]) for v in BIN])
    rows.append({"모델":m,"공통6_보정선형_셀MAE%p":round(e6,1),"전체8_보정선형_셀MAE%p":round(e8,1),"분할":f"층화 {int(FRAC*100)}/{100-int(FRAC*100)} × {REPS}회","seed":SEED})
df=pd.DataFrame(rows); write_sheets({"베이스라인_공통6_보정":df}); print(df.to_string(index=False))
