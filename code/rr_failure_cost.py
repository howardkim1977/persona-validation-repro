# -*- coding: utf-8 -*-
"""R2-12/m-i: 형식 위반 재생성의 1차 실패율·최종 제외율(모델·셀별)과 생성 규모(요청 수·문자량).
Gemini: 배치 라운드 요청 파일(r0/r1/r2)에서 라운드별 대상 수를 복원. 셀은 산출 CSV 의 _idx 로 결합.
EXAONE: 실행 로그의 재생성 메시지와 최종 산출의 _error 로 집계."""
import json, glob, re, os
import numpy as np, pandas as pd
from rr_common import write_sheets, AGES

def keys(paths):
    s=set()
    for p in paths:
        for line in open(p,encoding="utf-8"): s.add(int(json.loads(line)["key"][1:]))
    return s
rows=[]; cellrows=[]
for wave,out in [(2024,"outputs/synthetic_responses.csv"),(2025,"outputs/synthetic_2025.csv")]:
    r0=keys(glob.glob(f"outputs/batch_w{wave}_r0c*.jsonl")); r1=keys(glob.glob(f"outputs/batch_w{wave}_r1c*.jsonl")); r2=keys(glob.glob(f"outputs/batch_w{wave}_r2c*.jsonl"))
    d=pd.read_csv(out,encoding="utf-8-sig"); fin=int(d["_error"].notna().sum()) if "_error" in d else 0
    rows.append({"모델":"Gemini","차수":wave,"요청수(1차)":len(r0),"1차실패":len(r1),"1차실패율%":round(100*len(r1)/len(r0),2),
                 "2차실패":len(r2),"3차후잔여(최종제외)":fin,"최종제외율%":round(100*fin/len(r0),2)})
    for (g,a),sub in d.groupby(["성별","연령대"]):
        idx=set(sub["_idx"]); f1=len(idx&r1)
        cellrows.append({"모델":"Gemini","차수":wave,"성별":g,"연령대":a,"n":len(idx),"1차실패":f1,"1차실패율%":round(100*f1/len(idx),2)})
# EXAONE(live): 로그의 재생성 흔적 + 최종 _error
for wave,out,log in [(2024,"outputs/synthetic_exaone.csv","outputs/run_exaone.log"),(2025,"outputs/synthetic_exaone_2025.csv","outputs/run_exaone_2025.log")]:
    d=pd.read_csv(out,encoding="utf-8-sig"); n=len(d); fin=int(d["_error"].notna().sum()) if "_error" in d else 0
    txt=open(log,encoding="utf-8",errors="ignore").read() if os.path.exists(log) else ""
    n_fmt=len(re.findall(r"format|형식",txt)); n_rl=len(re.findall(r"429|레이트리밋",txt))
    rows.append({"모델":"EXAONE","차수":wave,"요청수(1차)":n,"1차실패":np.nan,"1차실패율%":np.nan,"2차실패":np.nan,
                 "3차후잔여(최종제외)":fin,"최종제외율%":round(100*fin/n,2),"비고":f"로그 형식관련 {n_fmt}줄, 레이트리밋 {n_rl}줄(1차 실패 개별 기록 없음)"})
    for (g,a),sub in d.groupby(["성별","연령대"]):
        e=int(sub["_error"].notna().sum()) if "_error" in sub else 0
        cellrows.append({"모델":"EXAONE","차수":wave,"성별":g,"연령대":a,"n":len(sub),"최종제외":e,"최종제외율%":round(100*e/len(sub),2)})
# 생성 규모: 배치 요청 문자량(시스템+사용자), 요청 수
vol=[]
for wave in [2024,2025]:
    chars=0; nreq=0
    for p in glob.glob(f"outputs/batch_w{wave}_r*c*.jsonl"):
        for line in open(p,encoding="utf-8"):
            o=json.loads(line); nreq+=1
            chars+=len(o["request"]["systemInstruction"]["parts"][0]["text"])+len(o["request"]["contents"][0]["parts"][0]["text"])
    vol.append({"모델":"Gemini(Batch)","차수":wave,"총요청수(재생성 포함)":nreq,"입력문자량(백만)":round(chars/1e6,2),"요청당 평균 입력문자":round(chars/nreq)})
fr=pd.DataFrame(rows); cr=pd.DataFrame(cellrows); vv=pd.DataFrame(vol)
write_sheets({"심사_형식실패":fr,"심사_형식실패_셀별":cr,"심사_생성규모":vv})
print(fr.to_string(index=False)); print(vv.to_string(index=False))
