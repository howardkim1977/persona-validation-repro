# -*- coding: utf-8 -*-
"""R2-12/m-i: 형식 위반 재생성의 1차 실패율·최종 제외율(모델·셀별)과 생성 규모(요청 수·문자량).
패키지 배치 기준으로 실행한다(패키지 루트에서 `python code/rr_failure_cost.py`).
Gemini: 라운드별 실패 수는 실행 콘솔 로그(logs/run_batch_*.log, run_demo_gemini.log)에서 복원.
  2024 본 실행의 배치 페이로드는 보존되지 않았고(PROTOCOL §4a), logs/batch_w2024_*.jsonl 은
  인구통계 전용 소거 실행의 페이로드이므로 셀별 1차 실패율과 문자량은 소거 실행 기준으로만 산출한다.
EXAONE: 최종 산출의 _error 로 제외 수를 집계(1차 실패 개별 기록 없음)."""
import json, glob, re, os
import numpy as np, pandas as pd
from rr_common import write_sheets

def rounds_from_log(path):
    """콘솔 로그에서 라운드별 (대상, 재생성) 수를 복원."""
    txt=open(path,encoding="utf-8",errors="ignore").read()
    r1=sum(int(x) for x in re.findall(r"성공 \d+ / 재생성 (\d+)",txt.split("[라운드 2]")[0]))
    tgt=[int(x) for x in re.findall(r"\[라운드 \d\] 대상 (\d+)건",txt)]
    n0=int(re.search(r"페르소나 (\d+)명",txt).group(1))
    return n0, r1, tgt   # 1차 대상, 1차 실패, 라운드별 대상 목록
def keys(paths):
    s=set()
    for p in paths:
        for line in open(p,encoding="utf-8"): s.add(int(json.loads(line)["key"][1:]))
    return s
rows=[]; cellrows=[]
runs=[("Gemini 2024 main run",2024,"logs/run_batch_full.log","outputs/synthetic_recoded_gemini.csv",None),
      ("Gemini 2025 run",2025,"logs/run_batch_2025.log","outputs/synthetic_recoded_2025_gemini.csv","logs/batch_w2025_r*c*.jsonl"),
      ("Gemini 2024 demographic-only ablation",2024,"logs/run_demo_gemini.log","outputs/synthetic_recoded_demo_gemini.csv","logs/batch_w2024_r*c*.jsonl"),
      ("Gemini 2024 temperature 0.7",2024,"logs/run_batch_t07.log","outputs/synthetic_recoded_gemini_t07.csv",None)]
for label,wave,log,out,pay in runs:
    n0,r1,tgt=rounds_from_log(log); r2=tgt[2] if len(tgt)>2 else 0
    rows.append({"실행":label,"차수":wave,"요청수(1차)":n0,"1차실패":r1,"1차실패율%":round(100*r1/n0,2),"2차실패":r2,
                 "총요청수":n0+sum(tgt[1:]),"최종제외":0,"최종제외율%":0.0,"근거":os.path.basename(log)})
    if pay:
        # 셀 소속은 페이로드의 시스템 지시문에서 직접 파싱(소거: '성별 남성, 연령대 10대'; 서사: '성별: 남자 / 나이: 19세')
        cell={}
        for pth in glob.glob(pay.replace("r*","r0")):
            for line in open(pth,encoding="utf-8"):
                o=json.loads(line); k=int(o["key"][1:]); t=o["request"]["systemInstruction"]["parts"][0]["text"]
                m=re.search(r"성별 (남성|여성), 연령대 (\S+?)\.",t)
                if m: g,a=m.group(1),m.group(2)
                else:
                    m=re.search(r"성별: (남자|여자) / 나이: (\d+)세",t); g={"남자":"남성","여자":"여성"}[m.group(1)]; age=int(m.group(2))
                    a="70대이상" if age>=70 else f"{(age//10)*10}대"
                cell[k]=(g,a)
        k1=keys(glob.glob(pay.replace("r*","r1")))
        df=pd.DataFrame([{"k":k,"성별":g,"연령대":a,"fail":k in k1} for k,(g,a) in cell.items()])
        for (g,a),sub in df.groupby(["성별","연령대"]):
            cellrows.append({"실행":label,"차수":wave,"성별":g,"연령대":a,"n":len(sub),"1차실패":int(sub.fail.sum()),"1차실패율%":round(100*sub.fail.mean(),2)})
# EXAONE(live): 패키지의 recoded 파일은 제외된 페르소나가 이미 빠져 있으므로 실행 로그의 추출 수에서 제외 수를 복원한다.
for label,wave,out,log in [("EXAONE 2024",2024,"outputs/synthetic_recoded_exaone.csv","logs/run_exaone.log"),("EXAONE 2025",2025,"outputs/synthetic_recoded_2025_exaone.csv","logs/run_exaone_2025.log")]:
    d=pd.read_csv(out,encoding="utf-8-sig"); n0=int(re.search(r"페르소나 (\d+)명",open(log,encoding="utf-8",errors="ignore").read()).group(1)); fin=n0-len(d)
    rows.append({"실행":label,"차수":wave,"요청수(1차)":n0,"1차실패":np.nan,"1차실패율%":np.nan,"2차실패":np.nan,"총요청수":np.nan,
                 "최종제외":fin,"최종제외율%":round(100*fin/n0,2),"근거":"live calls; 1차 실패 개별 기록 없음(logs/run_exaone*.log, recover_exaone.log)"})
fc=pd.read_csv("outputs/failure_rates_by_cell.csv",encoding="utf-8-sig")
for _,r in fc[fc["모델"].astype(str).str.upper().str.contains("EXAONE")].iterrows():
    cellrows.append({"실행":f"EXAONE {int(r['차수'])}","차수":int(r["차수"]),"성별":r["성별"],"연령대":r["연령대"],"n":int(r["목표_n"]),
                     "최종제외":int(r["목표_n"]-r["유효_n"]),"최종제외율%":round(float(r["형식실패율_%"]),2)})
vol=[]
for label,pat in [("Gemini 2025 run (archived payloads)","logs/batch_w2025_r*c*.jsonl"),("Gemini 2024 demographic-only ablation (archived payloads)","logs/batch_w2024_r*c*.jsonl")]:
    chars=0; nreq=0
    for p in glob.glob(pat):
        for line in open(p,encoding="utf-8"):
            o=json.loads(line); nreq+=1
            chars+=len(o["request"]["systemInstruction"]["parts"][0]["text"])+len(o["request"]["contents"][0]["parts"][0]["text"])
    vol.append({"실행":label,"총요청수(재생성 포함)":nreq,"입력문자량(백만)":round(chars/1e6,2),"요청당 평균 입력문자":round(chars/nreq)})
vol.append({"실행":"Gemini 2024 main run (payloads not preserved; estimate)","총요청수(재생성 포함)":rows[0]["총요청수"],"입력문자량(백만)":np.nan,"요청당 평균 입력문자":np.nan})
fr=pd.DataFrame(rows); cr=pd.DataFrame(cellrows); vv=pd.DataFrame(vol)
write_sheets({"심사_형식실패":fr,"심사_형식실패_셀별":cr,"심사_생성규모":vv})
print(fr.to_string(index=False)); print(vv.to_string(index=False))
