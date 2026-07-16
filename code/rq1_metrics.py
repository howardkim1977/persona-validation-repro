# -*- coding: utf-8 -*-
"""RQ1 지표 확장: 코사인 유사도·KL 발산(JS 포함)·문항평균 상관·MAE.
사후가중 합성 vs 가중 실측. 2024·2025 정답지 각각."""
import pandas as pd, numpy as np
BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CONS=["혁신성_기능","혁신성_쾌락","혁신성_사회","혁신성_인지","수용_성과기대","수용_노력기대","수용_사회영향","수용_촉진조건"]
CELL=["성별","연령대"]
a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig")
def wmean(df,v):
    s=df[[v,"WT"]].dropna(); return np.average(s[v],weights=s["WT"]) if len(s) else np.nan
def cwm(df,v): return {k:s[v].mean() for k,s in df.groupby(CELL)}
def postw(df,v,share):
    cm=cwm(df,v); num=sum(share.get(k,0)*cm[k] for k in cm if k in share and not np.isnan(cm[k]))
    den=sum(share.get(k,0) for k in cm if k in share and not np.isnan(cm[k])); return num/den if den else np.nan
def kl_bern(p,q,eps=1e-6):
    p=min(max(p,eps),1-eps); q=min(max(q,eps),1-eps)
    return p*np.log(p/q)+(1-p)*np.log((1-p)/(1-q))
def js_bern(p,q):
    m=(p+q)/2; return 0.5*kl_bern(p,m)+0.5*kl_bern(q,m)
def cosine(x,y):
    x,y=np.array(x),np.array(y); return float(x@y/(np.linalg.norm(x)*np.linalg.norm(y)))

models={"2024":{"Gemini":"outputs/synthetic_recoded_gemini.csv","EXAONE":"outputs/synthetic_recoded_exaone.csv"},
        "2025":{"Gemini":"outputs/synthetic_recoded_2025_gemini.csv","EXAONE":"outputs/synthetic_recoded_2025_exaone.csv"}}
rows=[]
for yr in ["2024","2025"]:
    ay=a[a.YEAR==int(yr)]; cw=ay.groupby(CELL)["WT"].sum(); share=(cw/cw.sum()).to_dict()
    act_bin=[wmean(ay,v) for v in BIN]
    has_cons = ay[CONS[0]].notna().any()
    act_cons=[wmean(ay,v) for v in CONS] if has_cons else None
    for m,f in models[yr].items():
        df=pd.read_csv(f,encoding="utf-8-sig")
        syn_bin=[postw(df,v,share) for v in BIN]
        mae=np.mean([abs(s-a_)*100 for s,a_ in zip(syn_bin,act_bin)])
        cos=cosine(act_bin,syn_bin)
        kl=np.mean([kl_bern(a_,s) for a_,s in zip(act_bin,syn_bin)])
        js=np.mean([js_bern(a_,s) for a_,s in zip(act_bin,syn_bin)])
        # 문항평균 상관: 척도 혼합(0~1 이진 + 1~5 구성)은 r을 부풀리므로 분리 보고
        r_bin=np.corrcoef(act_bin,syn_bin)[0,1]
        r_cons=np.nan
        if has_cons and all(c in df.columns for c in CONS):
            syn_cons=[postw(df,v,share) for v in CONS]
            r_cons=np.corrcoef(act_cons,syn_cons)[0,1]
        rows.append({"정답지":yr,"모델":m,"MAE_%p":round(mae,1),"코사인유사도":round(cos,4),
                     "KL발산_평균":round(kl,4),"JS발산_평균":round(js,4),
                     "r_이진8":round(r_bin,3),"r_구성8":round(r_cons,3) if not np.isnan(r_cons) else None})
res=pd.DataFrame(rows)
with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    res.to_excel(w,sheet_name="RQ1_지표종합",index=False)
print("워크북 시트 추가: RQ1_지표종합\n")
print(res.to_string(index=False))
