# -*- coding: utf-8 -*-
"""R2-5: 집단 간 오차 지표 보완. 기존 DPD_e(= 부호 오차의 최대−최소 범위)를
'between-group signed-error range' 로 개명하고, 최대 절대 집단오차·평균 절대 집단오차·
집단 간 SD·지표별 최악 집단을 함께 보고한다(14셀 전체 / 10대 제외 12셀)."""
import numpy as np, pandas as pd
from rr_common import *

real=Real(load_real(2024)); full=np.ones(real.n,bool)
RC={v:real.cell_wmean(full,v) for v in BIN}
rows=[]; worst=[]
for m,f in SYN_FILES.items():
    sc=syn_cell_means(load_syn(f))
    for subset,mask in [("14셀 전체",np.ones(NC,bool)),("10대 제외(12셀)",AGEC>0)]:
        rng_,mx,mn,sd=[],[],[],[]
        for v in BIN:
            e=((sc[v]-RC[v])*100)[mask]; e=e[~np.isnan(e)]
            rng_.append(e.max()-e.min()); mx.append(np.abs(e).max()); mn.append(np.abs(e).mean()); sd.append(e.std(ddof=1))
            if subset=="14셀 전체":
                k=int(np.argmax(np.abs((sc[v]-RC[v])*100))); c=CELLS[k]
                worst.append({"모델":m,"지표":v,"최악집단":f"{c[0]} {c[1]}","부호오차%p":round(((sc[v]-RC[v])*100)[k],1),
                              "범위%p":round(rng_[-1],1),"최대절대%p":round(mx[-1],1),"평균절대%p":round(mn[-1],1),"SD%p":round(sd[-1],1)})
        rows.append({"모델":m,"셀집합":subset,"집단간부호오차범위(구DPD_e)%p":round(np.mean(rng_),1),
                     "최대절대집단오차%p":round(np.mean(mx),1),"평균절대집단오차%p":round(np.mean(mn),1),"집단간오차SD%p":round(np.mean(sd),1)})
df=pd.DataFrame(rows); wf=pd.DataFrame(worst)
write_sheets({"심사_집단오차지표":df,"심사_집단오차_지표별":wf})
print(df.to_string(index=False)); print(wf.to_string(index=False))
