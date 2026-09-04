# -*- coding: utf-8 -*-
"""IV-D 문구 통제 실험의 검정(패키지 루트에서 실행).
두 arm(OTT 원문 / 중립 문구)은 동일 페르소나에 적용되었으나 페르소나 단위 짝 정보는 보존되지 않아
(outputs/framing_exp_*.json 은 arm별 집계만 담음) 독립 표본으로 분석한다:
  - 숏폼 이용률 변화의 95% CI: 두 arm 의 이항 표준오차(Wald) 결합
  - 두 비율 z-검정 p-값, 모델 2건에 대한 Holm 보정
  - P(숏폼|유튜브) 는 분모가 보존되지 않아 기술통계로만 보고."""
import json, math
import pandas as pd
from scipy.stats import norm
from rr_common import write_sheets
rows=[]; pv=[]
for m in ["gemini","exaone"]:
    d=json.load(open(f"outputs/framing_exp_{m}.json",encoding="utf-8"))
    n1,n2=d["n_ctrl"],d["n_treat"]; p1,p2=d["sf_ott"]/100,d["sf_neutral"]/100
    se=math.sqrt(p1*(1-p1)/n1+p2*(1-p2)/n2); diff=d["sf_delta"]; lo,hi=diff-1.96*se*100,diff+1.96*se*100   # 점추정은 저장된 비반올림 차이
    pp=(p1*n1+p2*n2)/(n1+n2); z=(p2-p1)/math.sqrt(pp*(1-pp)*(1/n1+1/n2)); p=2*norm.sf(abs(z)); pv.append(p)   # 생존함수로 언더플로 방지
    # 제외 민감도: 배정 N=1,144 전원 기준으로 제외자를 가장 불리하게(처치=전원 비이용, 통제=전원 이용)
    # 또는 가장 유리하게 배정했을 때 두 arm 차이가 가질 수 있는 범위. 신뢰구간이 아니라 결정적 경계다.
    N=1144
    t_lo=n2*p2/N; t_hi=(n2*p2+(N-n2))/N          # 처치 arm 의 전원 기준 이용률 범위
    c_lo=n1*p1/N; c_hi=(n1*p1+(N-n1))/N          # 통제 arm 의 전원 기준 이용률 범위
    d_lo=(t_lo-c_hi)*100; d_hi=(t_hi-c_lo)*100
    rows.append({"모델":d["model"],"n_통제":n1,"n_처치":n2,"숏폼_통제%":d["sf_ott"],"숏폼_처치%":d["sf_neutral"],"변화%p":round(diff,1),
                 "변화_CI_하한":round(lo,1),"변화_CI_상한":round(hi,1),"z":round(z,1),"p":p,"P(숏폼|유튜브)_통제%":d["cond_ott"],"P(숏폼|유튜브)_처치%":d["cond_neutral"],
                 "제외민감도_차이하한%p":round(d_lo,1),"제외민감도_차이상한%p":round(d_hi,1)})
# Holm(2건)
order=sorted(range(len(pv)),key=lambda i:pv[i]); adj=[None]*len(pv); prev=0
for rank,i in enumerate(order):
    a=min(1.0,max(prev,(len(pv)-rank)*pv[i])); adj[i]=a; prev=a
for r,a in zip(rows,adj): r["Holm_p"]=a
df=pd.DataFrame(rows); write_sheets({"심사_프레이밍검정":df}); print(df.to_string(index=False))
