# -*- coding: utf-8 -*-
"""R2-11: 구성개념(8개, 1~5점) 패널 내 상관구조·분산 비교(주장은 '평균 일치'로 축소, 진단으로 보고).
실측은 WT 가중 상관, 합성은 단순 상관. 요약: 비대각 28쌍 상관의 평균절대차, 두 상관벡터의 상관,
구성개념별 SD 비(합성/실측, 범위 압축 진단), 평균 차이."""
import numpy as np, pandas as pd
from rr_common import *

def wcorr(X,w):
    m=np.average(X,axis=0,weights=w); Xc=X-m; C=(Xc*w[:,None]).T@Xc/w.sum(); d=np.sqrt(np.diag(C)); return C/np.outer(d,d), np.sqrt(np.diag(C)), m
a=load_real(2024,with_hid=False)[CON+["WT"]].dropna()
Rr,SDr,Mr=wcorr(a[CON].to_numpy(float),a["WT"].to_numpy(float))
iu=np.triu_indices(len(CON),1)
summ=[]; long=[]
for m,f in SYN_FILES.items():
    s=load_syn(f)[CON].dropna(); X=s.to_numpy(float)
    Rs,SDs,Ms=wcorr(X,np.ones(len(X)))
    d=np.abs(Rs[iu]-Rr[iu])
    summ.append({"모델":m,"비대각28쌍_평균절대차":round(d.mean(),3),"최대절대차":round(d.max(),3),
                 "상관벡터간_Pearson":round(np.corrcoef(Rr[iu],Rs[iu])[0,1],3),
                 "실측_평균|r|":round(np.abs(Rr[iu]).mean(),3),"합성_평균|r|":round(np.abs(Rs[iu]).mean(),3),
                 "SD비(합성/실측)_평균":round(np.mean(SDs/SDr),3),"SD비_최소":round(np.min(SDs/SDr),3),"SD비_최대":round(np.max(SDs/SDr),3),
                 "평균차_MAE(1~5점)":round(np.mean(np.abs(Ms-Mr)),3)})
    for i,j in zip(*iu): long.append({"모델":m,"구성개념A":CON[i],"구성개념B":CON[j],"r_실측":round(Rr[i,j],3),"r_합성":round(Rs[i,j],3),"차이":round(Rs[i,j]-Rr[i,j],3)})
    for k,v in enumerate(CON): long.append({"모델":m,"구성개념A":v,"구성개념B":"(SD)","r_실측":round(SDr[k],3),"r_합성":round(SDs[k],3),"차이":round(SDs[k]-SDr[k],3)})
    print(f"[{m}] 상관 평균절대차 {summ[-1]['비대각28쌍_평균절대차']} | 벡터 상관 {summ[-1]['상관벡터간_Pearson']} | SD비 {summ[-1]['SD비(합성/실측)_평균']} | 평균차 {summ[-1]['평균차_MAE(1~5점)']}")
write_sheets({"심사_구성개념_상관요약":pd.DataFrame(summ),"심사_구성개념_상관행렬":pd.DataFrame(long)})
