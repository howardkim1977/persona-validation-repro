# -*- coding: utf-8 -*-
"""IV-A: 이진 8지표 문항평균 상관(Pearson)의 문항 부트스트랩 95% CI(B=5,000, seed 42).
입력: 워크북 시트 RQ1_정답지2024(실측 가중 비율, 합성 비율). 패키지 루트에서 실행."""
import numpy as np, pandas as pd
from rr_common import write_sheets, OUT_XLSX
d=pd.read_excel(OUT_XLSX,"RQ1_정답지2024"); real=d["실측2024"].to_numpy(float); rng=np.random.default_rng(42); rows=[]
for m in ["Gemini","EXAONE"]:
    syn=d[m].to_numpy(float); r0=np.corrcoef(real,syn)[0,1]; rs=[]
    for _ in range(5000):
        idx=rng.integers(0,len(real),len(real))
        if np.std(real[idx])==0 or np.std(syn[idx])==0: continue
        rs.append(np.corrcoef(real[idx],syn[idx])[0,1])
    lo,hi=np.percentile(rs,[2.5,97.5]); rows.append({"모델":m,"r_이진8":round(r0,3),"CI_하한":round(lo,2),"CI_상한":round(hi,2),"B":len(rs),"seed":42})
df=pd.DataFrame(rows); write_sheets({"심사_문항부트스트랩":df}); print(df.to_string(index=False))
