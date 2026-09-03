# -*- coding: utf-8 -*-
"""IV-A/IV-E 보조 통계(패키지 루트에서 실행): 2024·2025 이진 8지표의 중앙 절대오차와 leave-one-item-out MAE 범위.
입력: 워크북 시트 RQ1_정답지2024(2024 패널 vs 2024 실측), RQ1_2025문항셋(2025 matched-wave 패널 vs 2025 실측); 비율에서 직접 계산."""
import numpy as np, pandas as pd
from rr_common import write_sheets, OUT_XLSX
rows=[]
for yr,sheet,real in [(2024,"RQ1_정답지2024","실측2024"),(2025,"RQ1_2025문항셋","실측2025")]:
    d=pd.read_excel(OUT_XLSX,sheet)
    for m in ["Gemini","EXAONE"]:
        e=np.abs(d[m].to_numpy(float)-d[real].to_numpy(float))*100; loio=[np.delete(e,i).mean() for i in range(len(e))]
        rows.append({"차수":yr,"모델":m,"MAE%p":round(e.mean(),1),"중앙절대오차%p":round(float(np.median(e)),1),"LOIO_최소":round(min(loio),1),"LOIO_최대":round(max(loio),1),
                     "숏폼제외_MAE%p":round(e[d["변수"]!="숏폼_이용"].mean(),1),"숏폼제외_중앙값%p":round(float(np.median(e[d["변수"]!="숏폼_이용"])),1)})
df=pd.DataFrame(rows); write_sheets({"심사_문항보조통계":df}); print(df.to_string(index=False))
