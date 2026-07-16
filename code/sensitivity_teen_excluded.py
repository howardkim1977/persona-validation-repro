# -*- coding: utf-8 -*-
"""십대 셀 제외 전면 재분석(심사 대응 ③).

합성 10대 셀은 만 19세 페르소나로만 구성되어 실측 10대(10~19세)와 모집단이
정합하지 않는다. 이에 십대 셀을 양측에서 제외한 12셀(성별×20대~70대이상)
기준으로 다음을 전부 재산출하고, 전체(발표값 프로토콜) 수치와 병기한다.
  1) RQ1 전체 지표(2024·2025): MAE·코사인·KL·JS·r_이진·r_구성
  2) RQ2: 성별×연령 셀 MAE, DPD_e, 5축(성별·연령대·학력·직업유무·지역) 셀 MAE
  3) RQ3: 층화 30/70 반복 200회 보정(무보정/전역/연령회귀/실측직접)
  4) 시점 홀드아웃(2024 학습→2025 검정) + out-of-time 베이스라인
  5) 단순 베이스라인·서사 제거 분석(전체평균·전차수 2023·demo-only)
난수는 전용 rng(seed 42). 결과는 워크북 '십대제외_*' 시트에 기록한다.
학력·직업유무·지역 축은 페르소나 재표집(seed 고정)으로 속성을 재부착한다.
"""
import pandas as pd, numpy as np

BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CONS=["혁신성_기능","혁신성_쾌락","혁신성_사회","혁신성_인지","수용_성과기대","수용_노력기대","수용_사회영향","수용_촉진조건"]
CELL=["성별","연령대"]
AGES7=["10대","20대","30대","40대","50대","60대","70대이상"]
AGES6=AGES7[1:]                                   # 십대 제외
ACODE={x:i for i,x in enumerate(AGES7)}
REPS=200; SEED=42

a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig")
F24={"Gemini":"outputs/synthetic_recoded_gemini.csv","EXAONE":"outputs/synthetic_recoded_exaone.csv"}
F25={"Gemini":"outputs/synthetic_recoded_2025_gemini.csv","EXAONE":"outputs/synthetic_recoded_2025_exaone.csv"}
FDEMO={"Gemini":"outputs/synthetic_recoded_demo_gemini.csv","EXAONE":"outputs/synthetic_recoded_demo_exaone.csv"}
SYN24={m:pd.read_csv(f,encoding="utf-8-sig") for m,f in F24.items()}
SYN25={m:pd.read_csv(f,encoding="utf-8-sig") for m,f in F25.items()}

def wmean(df,v):
    s=df[[v,"WT"]].dropna(); return np.average(s[v],weights=s["WT"]) if len(s) else np.nan
def cwm_w(df,v):
    o={}
    for k,s in df.groupby(CELL):
        t=s[[v,"WT"]].dropna(); o[k]=np.average(t[v],weights=t["WT"]) if len(t) else np.nan
    return o
def cwm_s(df,v): return {k:s[v].mean() for k,s in df.groupby(CELL)}
def postw(df,v,share):
    cm=cwm_s(df,v); num=sum(share.get(k,0)*cm[k] for k in cm if k in share and not np.isnan(cm[k]))
    den=sum(share.get(k,0) for k in cm if k in share and not np.isnan(cm[k])); return num/den if den else np.nan
def kl_bern(p,q,eps=1e-6):
    p=min(max(p,eps),1-eps); q=min(max(q,eps),1-eps)
    return p*np.log(p/q)+(1-p)*np.log((1-p)/(1-q))
def js_bern(p,q):
    m=(p+q)/2; return 0.5*kl_bern(p,m)+0.5*kl_bern(q,m)
def cosine(x,y):
    x,y=np.array(x),np.array(y); return float(x@y/(np.linalg.norm(x)*np.linalg.norm(y)))

# ── 1) RQ1: 전체 vs 십대제외 ────────────────────────────────────────
def rq1_block(ay,syn,teen_excl):
    if teen_excl:
        ay=ay[ay["연령대"].isin(AGES6)]; syn=syn[syn["연령대"].isin(AGES6)]
    cw=ay.groupby(CELL)["WT"].sum(); share=(cw/cw.sum()).to_dict()
    act=[wmean(ay,v) for v in BIN]; sb=[postw(syn,v,share) for v in BIN]
    out={"MAE_%p":round(np.mean([abs(s-x)*100 for s,x in zip(sb,act)]),1),
         "코사인":round(cosine(act,sb),3),
         "KL":round(np.mean([kl_bern(x,s) for x,s in zip(act,sb)]),3),
         "JS":round(np.mean([js_bern(x,s) for x,s in zip(act,sb)]),3),
         "r_이진8":round(np.corrcoef(act,sb)[0,1],3)}
    if ay[CONS[0]].notna().any() and all(c in syn.columns for c in CONS):
        ac=[wmean(ay,v) for v in CONS]; sc=[postw(syn,v,share) for v in CONS]
        out["r_구성8"]=round(np.corrcoef(ac,sc)[0,1],3)
    return out
rq1_rows=[]
for yr,fs in [(2024,SYN24),(2025,SYN25)]:
    ay=a[a.YEAR==yr]
    for m,syn in fs.items():
        for te in [False,True]:
            rq1_rows.append({"정답지":yr,"모델":m,"표본":"십대제외" if te else "전체(발표)",
                             **rq1_block(ay,syn,te)})
rq1=pd.DataFrame(rq1_rows)
print("=== 1) RQ1 전체 vs 십대제외 ===");print(rq1.to_string(index=False))

# ── 2) RQ2: 셀 MAE·DPD_e·5축 ────────────────────────────────────────
a24=a[(a.YEAR==2024)&(a["연령대"].isin(AGES6))]
a24_full=a[(a.YEAR==2024)&(a["연령대"].isin(AGES7))]
rq2_rows=[]
for m,syn in SYN24.items():
    syn6=syn[syn["연령대"].isin(AGES6)]
    for lab,ad,sd,ages in [("전체(발표)",a24_full,syn,AGES7),("십대제외",a24,syn6,AGES6)]:
        errs=[];rngs=[]
        for v in BIN:
            ac=cwm_w(ad,v); sc=cwm_s(sd,v)
            ks=[k for k in ac if k in sc and not np.isnan(ac[k]) and not np.isnan(sc[k])]
            e=[(sc[k]-ac[k])*100 for k in ks]
            errs+= [abs(x) for x in e]; rngs.append(max(e)-min(e))
        # 축 MAE: 성별·연령대
        ax={}
        for axis in ["성별","연령대"]:
            per=[]
            for v in BIN:
                es=[]
                for g,s_ in ad.groupby(axis):
                    t=s_[[v,"WT"]].dropna()
                    if not len(t): continue
                    act=np.average(t[v],weights=t["WT"]); sv=sd[sd[axis]==g][v].mean()
                    if not np.isnan(sv): es.append(abs(sv-act)*100)
                per.append(np.mean(es))
            ax[axis]=round(np.mean(per),1)
        rq2_rows.append({"모델":m,"표본":lab,"셀MAE%p":round(np.mean(errs),1),
                         "DPD_e%p":round(np.mean(rngs),1),"성별축%p":ax["성별"],"연령대축%p":ax["연령대"]})
rq2=pd.DataFrame(rq2_rows)
print("\n=== 2) RQ2 셀 MAE·DPD_e·성별/연령 축 ===");print(rq2.to_string(index=False))

# ── 3) RQ3: 200분할 보정(십대제외 12셀) ─────────────────────────────
def rq3_splits(ad,syn,ages):
    rng=np.random.default_rng(SEED)
    ad=ad.reset_index(drop=True)
    unc=[];glo=[];reg=[];rdir=[]
    for _ in range(REPS):
        ad=ad.copy(); ad["_c"]=False
        for _,idx in ad.groupby(CELL).groups.items():
            idx=list(idx); rng.shuffle(idx); ad.loc[idx[:int(len(idx)*0.3)],"_c"]=True
        cal=ad[ad._c]; tst=ad[~ad._c]
        u=[];g=[];r=[];d=[]
        for v in BIN:
            sc=cwm_s(syn,v); cc=cwm_w(cal,v); tc=cwm_w(tst,v)
            gmc=wmean(cal,v)
            ks=[k for k in sc if k in tc and not np.isnan(tc[k])]
            u+=[abs(sc[k]-tc[k]) for k in ks]
            bs=[sc[k]-cc[k] for k in cc if k in sc and not np.isnan(cc[k])]
            b=np.mean(bs) if bs else 0
            g+=[abs((sc[k]-b)-tc[k]) for k in ks]
            xs=[(ACODE[k[1]],sc[k]-cc[k]) for k in cc if k in sc and not np.isnan(cc[k])]
            if len(xs)>=3:
                X=np.array([x for x,_ in xs]);Y=np.array([y for _,y in xs]);sl,ic=np.polyfit(X,Y,1)
                r+=[abs((sc[k]-(sl*ACODE[k[1]]+ic))-tc[k]) for k in ks]
            d+=[abs((cc[k] if k in cc and not np.isnan(cc[k]) else gmc)-tc[k]) for k in ks]
        unc.append(np.mean(u)*100);glo.append(np.mean(g)*100);reg.append(np.mean(r)*100);rdir.append(np.mean(d)*100)
    return round(np.mean(unc),1),round(np.mean(glo),1),round(np.mean(reg),1),round(np.mean(rdir),1)
rq3_rows=[]
for m,syn in SYN24.items():
    for lab,ad,sd in [("전체(발표)",a24_full,syn),("십대제외",a24,syn[syn["연령대"].isin(AGES6)])]:
        u,g,r,d=rq3_splits(ad,sd,AGES6 if lab=="십대제외" else AGES7)
        rq3_rows.append({"모델":m,"표본":lab,"무보정%p":u,"전역%p":g,"연령회귀%p":r,"실측직접%p":d})
rq3=pd.DataFrame(rq3_rows)
print("\n=== 3) RQ3 보정(200분할) ===");print(rq3.to_string(index=False))

# ── 4) 시점 홀드아웃 + out-of-time 베이스라인(십대제외) ──────────────
a25=a[(a.YEAR==2025)&(a["연령대"].isin(AGES6))]
a25_full=a[(a.YEAR==2025)&(a["연령대"].isin(AGES7))]
a24y={True:a24,False:a24_full}; a25y={True:a25,False:a25_full}
th_rows=[]
for m in SYN24:
    s24=SYN24[m]; s25=SYN25[m]
    for te in [False,True]:
        ad24=a24y[te]; ad25=a25y[te]
        s24_=s24[s24["연령대"].isin(AGES6)] if te else s24
        s25_=s25[s25["연령대"].isin(AGES6)] if te else s25
        unc=[];reg=[];gm=[];prev=[]
        for v in BIN:
            sc24=cwm_s(s24_,v); ac24=cwm_w(ad24,v); sc25=cwm_s(s25_,v); ac25=cwm_w(ad25,v)
            ks=[k for k in sc25 if k in ac25 and not np.isnan(ac25[k])]
            bk=[k for k in sc24 if k in ac24 and not np.isnan(ac24[k])]
            xs=[(ACODE[k[1]],sc24[k]-ac24[k]) for k in bk]
            sl,ic=np.polyfit([x for x,_ in xs],[y for _,y in xs],1) if len(xs)>=3 else (0,np.mean([y for _,y in xs]))
            t25=ad25[[v,"WT"]].dropna(); g25=np.average(t25[v],weights=t25["WT"])
            unc+=[abs(sc25[k]-ac25[k]) for k in ks]
            reg+=[abs((sc25[k]-(sl*ACODE[k[1]]+ic))-ac25[k]) for k in ks]
            gm+=[abs(g25-ac25[k]) for k in ks]
            prev+=[abs(ac24[k]-ac25[k]) for k in ks if k in ac24 and not np.isnan(ac24[k])]
        th_rows.append({"모델":m,"표본":"십대제외" if te else "전체(발표)",
                        "시점밖무보정%p":round(np.mean(unc)*100,1),"시점밖연령회귀%p":round(np.mean(reg)*100,1),
                        "전체평균BL%p":round(np.mean(gm)*100,1),"전차수BL%p":round(np.mean(prev)*100,1)})
th=pd.DataFrame(th_rows)
print("\n=== 4) 시점 홀드아웃 + out-of-time 베이스라인 ===");print(th.to_string(index=False))

# ── 5) 단순 베이스라인·서사 제거(십대제외) ──────────────────────────
a23=a[a.YEAR==2023]
bl_rows=[]
for te in [False,True]:
    ad=a24y[te]; ages=AGES6 if te else AGES7
    gm_e=[];prev_e=[]
    for v in BIN:
        ac=cwm_w(ad,v); grand=wmean(ad,v)
        pc=cwm_w(a23[a23["연령대"].isin(ages)],v) if v in a23 and a23[v].notna().any() else {}
        ks=[k for k in ac if not np.isnan(ac[k])]
        gm_e+=[abs(grand-ac[k]) for k in ks]
        prev_e+=[abs(pc[k]-ac[k]) for k in ks if k in pc and not np.isnan(pc[k])]
    row={"표본":"십대제외" if te else "전체(발표)",
         "전체평균BL%p":round(np.mean(gm_e)*100,1),"전차수2023BL%p":round(np.mean(prev_e)*100,1)}
    for m in FDEMO:
        dm=pd.read_csv(FDEMO[m],encoding="utf-8-sig")
        dm=dm[dm["연령대"].isin(ages)]
        errs=[]
        for v in BIN:
            ac=cwm_w(ad,v); sc=cwm_s(dm,v)
            errs+=[abs(sc[k]-ac[k])*100 for k in ac if k in sc and not np.isnan(ac[k]) and not np.isnan(sc[k])]
        row[f"demo-only_{m}%p"]=round(np.mean(errs),1)
    bl_rows.append(row)
bl=pd.DataFrame(bl_rows)
print("\n=== 5) 베이스라인·서사 제거 ===");print(bl.to_string(index=False))

# ── 6) 학력·직업유무·지역 축(페르소나 재부착, 십대제외) ──────────────
ax_rows=[]
try:
    from generate import sample_personas
    EDU_MAP={"초졸이하":"초졸이하","중졸":"중졸이하","고졸":"고졸이하","전문대졸":"대졸이하",
             "대졸":"대졸이하","대학원졸":"대학원이상"}
    AREA={1:"서울",2:"부산",3:"대구",4:"인천",5:"광주",6:"대전",7:"울산",8:"경기",9:"강원",
          10:"충북",11:"충남",12:"전북",13:"전남",14:"경북",15:"경남",16:"제주",17:"세종"}
    FULL2SHORT={"서울특별시":"서울","부산광역시":"부산","대구광역시":"대구","인천광역시":"인천",
      "광주광역시":"광주","대전광역시":"대전","울산광역시":"울산","세종특별자치시":"세종","경기도":"경기",
      "강원특별자치도":"강원","충청북도":"충북","충청남도":"충남","전북특별자치도":"전북","전라남도":"전남",
      "경상북도":"경북","경상남도":"경남","제주특별자치도":"제주"}
    def emp(occ):
        o=str(occ)
        return "무직" if any(k in o for k in ["무직","주부","학생","군인","없음","실업"]) else "유직"
    ps=sample_personas("analysis_ready.csv","nemotron_personas_korea.csv",2024)
    idx2={i:{"학력":EDU_MAP.get(p["segments"]["교육수준"]),"직업유무":emp(p["segments"]["직업"]),
             "지역":FULL2SHORT.get(p["segments"]["시도"])} for i,p in enumerate(ps)}
    ad=a24.copy(); ad["_학력"]=ad["학력"]; ad["_직업유무"]=ad["직업유무"] if "직업유무" in ad else np.nan
    ad["_지역"]=ad["지역"].map(AREA)
    RAW={"Gemini":"outputs/synthetic_responses.csv","EXAONE":"outputs/synthetic_exaone.csv"}
    for m in SYN24:
        raw=pd.read_csv(RAW[m],encoding="utf-8-sig")
        order=raw["_idx"].tolist() if "_error" not in raw else raw.loc[raw["_error"].isna(),"_idx"].tolist()
        rec=SYN24[m].reset_index(drop=True).copy()
        rec["_학력"]=[idx2[i]["학력"] for i in order]
        rec["_직업유무"]=[idx2[i]["직업유무"] for i in order]
        rec["_지역"]=[idx2[i]["지역"] for i in order]
        rec=rec[rec["연령대"].isin(AGES6)]
        for axis,acol in [("학력","_학력"),("직업유무","_직업유무"),("지역","_지역")]:
            if acol=="_직업유무" and ad[acol].isna().all():
                # 실측 직업유무는 원 스키마 컬럼(직업유무)을 사용
                ad[acol]=ad["직업유무"]
            per=[]
            for v in BIN:
                es=[]
                for g in set(ad[acol].dropna())&set(rec[acol].dropna()):
                    t=ad[ad[acol]==g][[v,"WT"]].dropna()
                    if not len(t): continue
                    act=np.average(t[v],weights=t["WT"]); sv=rec[rec[acol]==g][v].mean()
                    if not np.isnan(sv): es.append(abs(sv-act)*100)
                per.append(np.mean(es))
            ax_rows.append({"모델":m,"축":axis,"표본":"십대제외","셀MAE%p":round(np.mean(per),1)})
    axdf=pd.DataFrame(ax_rows)
    print("\n=== 6) 학력·직업유무·지역 축(십대제외) ===");print(axdf.to_string(index=False))
except Exception as e:
    axdf=pd.DataFrame([{"오류":str(e)[:200]}])
    print(f"\n[경고] 축 재부착 실패: {e}")

# ── 기록 ────────────────────────────────────────────────────────────
with pd.ExcelWriter("outputs/validity_results.xlsx",engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
    rq1.to_excel(w,sheet_name="십대제외_RQ1",index=False)
    rq2.to_excel(w,sheet_name="십대제외_RQ2",index=False)
    rq3.to_excel(w,sheet_name="십대제외_RQ3보정",index=False)
    th.to_excel(w,sheet_name="십대제외_시점홀드아웃",index=False)
    bl.to_excel(w,sheet_name="십대제외_베이스라인",index=False)
    axdf.to_excel(w,sheet_name="십대제외_추가축",index=False)
print("\n워크북 시트 추가: 십대제외_RQ1/RQ2/RQ3보정/시점홀드아웃/베이스라인/추가축")
