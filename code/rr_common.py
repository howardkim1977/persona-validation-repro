# -*- coding: utf-8 -*-
"""심사 대응 분석 공통 모듈(IEEE Access 재투고, 2026-09).

rq3_realonly.py 의 벡터화 설계를 공유한다: 2024 실측(연령대 7개 밴드, 가구 ID 결합),
14개 성별×연령 셀의 고정 순서, 가중 셀평균, 층화/가구 분할, 합성 셀평균 사전계산.
모든 심사 대응 스크립트(rr_*.py)가 동일한 자료·셀 정의·난수 규약을 쓰도록 한다."""
import pandas as pd, numpy as np
from recode import recode

BIN=["AI_이용여부","OTT_이용","유튜브_이용","숏폼_이용","SNS_이용","메신저_이용","메타버스_이용","콘텐츠구독_이용"]
CON=["혁신성_기능","혁신성_쾌락","혁신성_사회","혁신성_인지","수용_성과기대","수용_노력기대","수용_사회영향","수용_촉진조건"]
CELL=["성별","연령대"]; AGES=["10대","20대","30대","40대","50대","60대","70대이상"]
ACODE={x:i for i,x in enumerate(AGES)}
CELLS=[(s,g) for s in ["남성","여성"] for g in AGES]; CIDX={c:i for i,c in enumerate(CELLS)}; NC=len(CELLS)
SEXD=np.array([1.0 if c[0]=="여성" else 0.0 for c in CELLS]); AGEC=np.array([float(ACODE[c[1]]) for c in CELLS])
SEED=42
SYN_FILES={"Gemini":"outputs/synthetic_recoded_gemini.csv","EXAONE":"outputs/synthetic_recoded_exaone.csv"}
OUT_XLSX="outputs/validity_results.xlsx"


def load_real(year=2024, with_hid=True):
    a=pd.read_csv("analysis_ready.csv",encoding="utf-8-sig")
    d=a[(a.YEAR==year)&(a["연령대"].isin(AGES))].copy().reset_index(drop=True)
    if with_hid:
        hid=pd.read_csv("private/PanelData_20260701.csv",encoding="utf-8-sig",usecols=["OPID","hid"]).drop_duplicates("OPID")
        d=d.merge(hid,on="OPID",how="left")
    d["_cell"]=[CIDX[(s,g)] for s,g in zip(d["성별"],d["연령대"])]
    return d


def load_syn(path):
    s=pd.read_csv(path,encoding="utf-8-sig")
    s=s[s["연령대"].isin(AGES)].copy().reset_index(drop=True)
    s["_cell"]=[CIDX[(g,a)] for g,a in zip(s["성별"],s["연령대"])]
    return s


def syn_cell_means(s, vars_=BIN):
    """합성 셀평균 dict {var: (NC,)}"""
    out={}
    for v in vars_:
        g=s.groupby(CELL)[v].mean()
        out[v]=np.array([g.get(c,np.nan) for c in CELLS])
    return out


class Real:
    """실측 배열 래퍼: 가중 셀평균·전체평균·셀 표본수 계산(mask 기반, 벡터화)."""
    def __init__(self, d, vars_=BIN):
        self.d=d; self.n=len(d)
        self.cell=d["_cell"].to_numpy(); self.wt=d["WT"].to_numpy(float)
        self.Y={v:d[v].to_numpy(float) for v in vars_}
        self.hh=d["hid"].to_numpy() if "hid" in d else None
    def cell_wmean(self,mask,v):
        y=self.Y[v]; ok=mask&~np.isnan(y)
        num=np.bincount(self.cell[ok],weights=(y*self.wt)[ok],minlength=NC)
        den=np.bincount(self.cell[ok],weights=self.wt[ok],minlength=NC)
        with np.errstate(invalid="ignore"): return np.where(den>0,num/den,np.nan)
    def cell_n(self,mask):
        return np.bincount(self.cell[mask],minlength=NC)
    def cell_neff(self,mask,v=None):
        """셀별 Kish 유효 표본수. v 를 주면 그 항목의 결측을 제외한다.

        셀평균(cell_wmean)이 항목 결측을 제외하므로, 그 평균의 표집분산 근사에
        쓰는 유효 표본수도 같은 응답자 집합에서 계산해야 한다."""
        if v is not None: mask=mask&~np.isnan(self.Y[v])
        w=self.wt; out=np.zeros(NC)
        for c in range(NC):
            m=mask&(self.cell==c)
            if m.any(): out[c]=w[m].sum()**2/np.sum(w[m]**2)
        return out
    def grand_wmean(self,mask,v):
        y=self.Y[v]; ok=mask&~np.isnan(y)
        return np.average(y[ok],weights=self.wt[ok]) if ok.any() else np.nan
    def cell_share(self,mask=None):
        m=np.ones(self.n,bool) if mask is None else mask
        cw=np.bincount(self.cell[m],weights=self.wt[m],minlength=NC); return cw/cw.sum()
    def overall_wmean(self,v,mask=None):
        m=np.ones(self.n,bool) if mask is None else mask
        y=self.Y[v]; ok=m&~np.isnan(y); return np.average(y[ok],weights=self.wt[ok])


def stratified_split(rng, real, frac):
    """셀 내 층화 무작위 분할(비가중 개인 수 기준). 보정셋 마스크 반환."""
    m=np.zeros(real.n,bool)
    for c in range(NC):
        idx=np.where(real.cell==c)[0]; rng.shuffle(idx); m[idx[:int(len(idx)*frac)]]=True
    return m


def household_resample_index(rng, real):
    """가구 군집 복원추출 → 행 인덱스 배열(가중·군집 구조 보존)."""
    hh=real.hh; uniq,inv=np.unique(hh,return_inverse=True)
    groups=[np.where(inv==i)[0] for i in range(len(uniq))]
    pick=rng.integers(0,len(uniq),len(uniq))
    return np.concatenate([groups[i] for i in pick])


def post_stratified_rate(real_share, syn_cell):
    """합성 셀평균을 실측 가중 셀 점유율로 사후층화한 전체 추정치."""
    ok=~np.isnan(syn_cell); return np.sum(real_share[ok]*syn_cell[ok])/np.sum(real_share[ok])


def write_sheets(sheets: dict):
    with pd.ExcelWriter(OUT_XLSX,engine="openpyxl",mode="a",if_sheet_exists="replace") as w:
        for name,df in sheets.items(): df.to_excel(w,sheet_name=name,index=False)
    print("워크북 시트 갱신:", ", ".join(sheets))


def boot_p(d):
    """양측 부트스트랩 p값(add-one 규약, Davison & Hinkley 1997).

    p = min{1, 2 * min(#{d<=0}+1, #{d>=0}+1) / (B+1)}.
    복제 전부가 한쪽에 있을 때의 최소값이 1/B 가 아니라 2/(B+1) 이 되어
    복제 수가 유한한 데서 오는 하한을 과소평가하지 않는다."""
    d=np.asarray(d,float); B=len(d)
    k=min(int((d<=0).sum()),int((d>=0).sum()))
    return min(1.0, 2.0*(k+1)/(B+1))


def holm(pvals):
    """Holm 단계적 보정 p값(입력 순서 유지)."""
    p=np.asarray(pvals,float); m=len(p); order=np.argsort(p); adj=np.empty(m)
    run=0.0
    for rank,i in enumerate(order):
        run=max(run,(m-rank)*p[i]); adj[i]=min(1.0,run)
    return adj
