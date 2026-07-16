# -*- coding: utf-8 -*-
"""k2·k3 잔여 실패를 저동시성(workers=8)으로 순차 복구·병합."""
import os, sys
from dotenv import dotenv_values
os.environ.update({k:v for k,v in dotenv_values(".env").items() if v})
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from generate import sample_personas, ExaoneClient, generate_one
ps=sample_personas("analysis_ready.csv","nemotron_personas_korea.csv",2024)
client=ExaoneClient(1.0)
def recover(path):
    d=pd.read_csv(path,encoding="utf-8-sig")
    fail=sorted(d[d["_error"].notna()]["_idx"].astype(int).tolist())
    print(f"[{path}] 복구 대상 {len(fail)}",flush=True)
    def work(i):
        a=generate_one(client,ps[i],2024)
        a.update({"_idx":i,"_model":"exaone","_wave":2024,"성별":ps[i]["gender"],"연령대":ps[i]["age"]})
        return i,a
    new={}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs=[ex.submit(work,i) for i in fail]
        done=0
        for f in as_completed(futs):
            i,a=f.result(); new[i]=a; done+=1
            if done%100==0: print(f"  {done}/{len(fail)}",flush=True)
    d=d.set_index("_idx"); still=0
    for i,a in new.items():
        bad="_error" in a and a.get("_error")
        if bad: still+=1
        for k,v in a.items():
            if k=="_idx": continue
            if k not in d.columns: d[k]=pd.NA
            d.loc[i,k]=v
        if not bad: d.loc[i,"_error"]=pd.NA
    d=d.reset_index().sort_values("_idx")
    d.to_csv(path,index=False,encoding="utf-8-sig")
    print(f"[{path}] 병합 완료 | 잔여 {still} → 최종 오류 {int(d['_error'].notna().sum())}",flush=True)
recover("outputs/synthetic_exaone_k2.csv")
recover("outputs/synthetic_exaone_k3.csv")
print("전체 복구 완료")
