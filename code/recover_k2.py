# -*- coding: utf-8 -*-
"""pass2 실패행(_error)만 재생성·병합(max_tokens 4096)."""
import os
from dotenv import dotenv_values
os.environ.update({k:v for k,v in dotenv_values(".env").items() if v})
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from generate import sample_personas, ExaoneClient, generate_one
OUT="outputs/synthetic_exaone_k2.csv"
d=pd.read_csv(OUT,encoding="utf-8-sig")
fail=sorted(d[d["_error"].notna()]["_idx"].astype(int).tolist())
print(f"복구 대상 {len(fail)}건")
ps=sample_personas("analysis_ready.csv","nemotron_personas_korea.csv",2024)
assert len(ps)==len(d)
client=ExaoneClient(1.0)
def work(i):
    a=generate_one(client,ps[i],2024)
    a.update({"_idx":i,"_model":"exaone","_wave":2024,"성별":ps[i]["gender"],"연령대":ps[i]["age"]})
    return i,a
new={}
with ThreadPoolExecutor(max_workers=24) as ex:
    futs=[ex.submit(work,i) for i in fail]
    done=0
    for f in as_completed(futs):
        i,a=f.result(); new[i]=a; done+=1
        if done%200==0: print(f"  {done}/{len(fail)}",flush=True)
d=d.set_index("_idx")
still=0
for i,a in new.items():
    bad="_error" in a and a.get("_error")
    if bad: still+=1
    for k,v in a.items():
        if k=="_idx": continue
        if k not in d.columns: d[k]=pd.NA
        d.loc[i,k]=v
    if not bad: d.loc[i,"_error"]=pd.NA
d=d.reset_index().sort_values("_idx")
d.to_csv(OUT,index=False,encoding="utf-8-sig")
print(f"병합 완료 | 잔여 실패 {still} → 최종 오류 {int(d['_error'].notna().sum())}")
