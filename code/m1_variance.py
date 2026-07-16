# -*- coding: utf-8 -*-
"""M1: 페르소나당 복수응답(K회)으로 생성 확률성(within) vs 페르소나 이질성(between) 분해.
사용: python m1_variance.py {gemini|exaone} [K] [N]"""
import sys, json
import numpy as np, pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from generate import (sample_personas, GeminiClient, ExaoneClient, generate_one)
BIN=["p__d31002","p__d26001","p__d26075","p__d26092","p__d11001","p__d22001","p__d28001","p__d29001"]
NAME={"p__d31002":"AI","p__d26001":"OTT","p__d26075":"유튜브","p__d26092":"숏폼",
      "p__d11001":"SNS","p__d22001":"메신저","p__d28001":"메타버스","p__d29001":"구독"}
model=sys.argv[1]; K=int(sys.argv[2]) if len(sys.argv)>2 else 5; N=int(sys.argv[3]) if len(sys.argv)>3 else 200
ps=sample_personas("analysis_ready.csv","nemotron_personas_korea.csv",2024,limit=N)
client=GeminiClient(1.0) if model=="gemini" else ExaoneClient(1.0)
print(f"{model}: 페르소나 {len(ps)}명 × {K}회 응답 생성")
def one(i,k):
    ans=generate_one(client,ps[i],2024)
    return i,{c:(1 if ans.get(c)==1 else 0) for c in BIN if isinstance(ans.get(c),int)}
rows={i:[] for i in range(len(ps))}
workers=8 if model=="gemini" else 4
with ThreadPoolExecutor(max_workers=workers) as ex:
    futs=[ex.submit(one,i,k) for i in range(len(ps)) for k in range(K)]
    done=0
    for f in as_completed(futs):
        i,d=f.result(); rows[i].append(d); done+=1
        if done%100==0: print(f"  {done}/{len(ps)*K}",flush=True)
# 분산 분해(이진 문항): within = 평균 셀내분산, between = 페르소나 평균의 분산
print(f"\n[{model}] 문항별 분산분해 (within=생성노이즈, between=페르소나이질성, ICC=between/(within+between))")
res=[]
for c in BIN:
    pmeans=[]; wvars=[]
    for i in rows:
        vals=[r[c] for r in rows[i] if c in r]
        if len(vals)>=2: pmeans.append(np.mean(vals)); wvars.append(np.var(vals,ddof=0))
    if len(pmeans)<10: continue
    within=np.mean(wvars); between=np.var(pmeans,ddof=1)
    icc=between/(within+between) if (within+between)>0 else np.nan
    res.append({"문항":NAME[c],"within":round(within,4),"between":round(between,4),"ICC":round(icc,3)})
    print(f"  {NAME[c]:<8} within {within:.4f}  between {between:.4f}  ICC {icc:.3f}")
df=pd.DataFrame(res)
print(f"\n평균 ICC: {df['ICC'].mean():.3f}  (1에 가까울수록 응답이 페르소나로 결정, 0이면 생성노이즈 지배)")
df.to_csv(f"outputs/m1_variance_{model}.csv",index=False,encoding="utf-8-sig")
print(f"저장: outputs/m1_variance_{model}.csv")
