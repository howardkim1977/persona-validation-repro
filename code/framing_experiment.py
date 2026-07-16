# -*- coding: utf-8 -*-
"""통제 재생성: 숏폼 문항 '문구만' 조작하여 프레이밍(단어 'OTT') 효과를 격리.
동일 2024 문항셋·동일 페르소나(시드 고정)에 두 문구를 적용하는 짝지음(paired) 설계.
  통제(OTT):   '숏폼(short form) 형태의 OTT 서비스를 이용한 적이 있습니까?'  (원 설문)
  처치(중립):  'YouTube 쇼츠, 인스타그램 릴스, 틱톡과 같은 짧은 동영상(숏폼)을 이용한 적이 있습니까?'
다른 35개 문항·모델·온도·페르소나는 모두 동일 → 유일한 차이는 숏폼 문항 문구.
"""
import os, sys, argparse, concurrent.futures as cf
import numpy as np
from dotenv import load_dotenv
load_dotenv()
import generate
from generate import sample_personas, generate_one, GeminiClient, ExaoneClient

SF = "p__d26092"; YT = "p__d26075"
OTT_TEXT = generate.ITEMS_BY_WAVE[2024][SF][0]                      # 원 문구(통제)
NEUTRAL_TEXT = "YouTube 쇼츠, 인스타그램 릴스, 틱톡과 같은 짧은 동영상(숏폼)을 이용한 적이 있습니까?"
OPTS = generate.ITEMS_BY_WAVE[2024][SF][1]                          # {1:예,2:아니오}

def run_batch(personas, client, workers):
    """각 페르소나 1회 응답 → (숏폼이용0/1, 유튜브이용0/1) 또는 None(오류)."""
    def one(p):
        r = generate_one(client, p, 2024)
        if "_error" in r or SF not in r: return None
        return (1 if r.get(SF)==1 else 0, 1 if r.get(YT)==1 else 0)
    out=[]
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for res in ex.map(one, personas): out.append(res)
    return out

def stats(res):
    v=[r for r in res if r]
    sf=np.array([r[0] for r in v]); yt=np.array([r[1] for r in v])
    sf_rate=sf.mean()*100
    m=yt==1; cond=(sf[m].mean()*100) if m.sum() else float('nan')
    return len(v), sf_rate, cond

def boot_ci(a, B=2000, seed=1):
    rng=np.random.default_rng(seed); a=np.array(a)
    bs=[a[rng.integers(0,len(a),len(a))].mean()*100 for _ in range(B)]
    return np.percentile(bs,2.5), np.percentile(bs,97.5)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--model",choices=["gemini","exaone"],default="gemini")
    ap.add_argument("--limit",type=int,default=1200)
    ap.add_argument("--workers",type=int,default=12)
    a=ap.parse_args()

    personas=sample_personas("analysis_ready.csv","nemotron_personas_korea.csv",2024,seed=42,limit=a.limit)
    print(f"[표집] 페르소나 {len(personas)}명 (시드42, 동일 표본에 두 문구 적용)")
    client = GeminiClient(temperature=1.0) if a.model=="gemini" else ExaoneClient(temperature=1.0)

    # 통제(OTT 원문)
    generate.ITEMS_BY_WAVE[2024][SF]=(OTT_TEXT, OPTS)
    print(f"[통제] 문구: {OTT_TEXT}")
    ctrl=run_batch(personas, client, a.workers)
    # 처치(중립)
    generate.ITEMS_BY_WAVE[2024][SF]=(NEUTRAL_TEXT, OPTS)
    print(f"[처치] 문구: {NEUTRAL_TEXT}")
    treat=run_batch(personas, client, a.workers)

    nc,cs,cc = stats(ctrl); nt,ts,tc = stats(treat)
    cvals=[r[0] for r in ctrl if r]; tvals=[r[0] for r in treat if r]
    clo,chi=boot_ci(cvals); tlo,thi=boot_ci(tvals)
    print("\n"+"="*64)
    print(f"통제 재생성 결과 ({a.model}, n_valid 통제 {nc}/처치 {nt})")
    print("="*64)
    print(f"  숏폼 이용률   통제(OTT)  {cs:.1f}%  [95%CI {clo:.1f},{chi:.1f}]")
    print(f"               처치(중립) {ts:.1f}%  [95%CI {tlo:.1f},{thi:.1f}]")
    print(f"               → 문구 효과 Δ = {ts-cs:+.1f}%p")
    print(f"  P(숏폼|유튜브) 통제(OTT)  {cc:.1f}%   처치(중립) {tc:.1f}%   Δ={tc-cc:+.1f}%p")
    print(f"  (참고 실측 2024: 숏폼 69.6%, P(숏폼|유튜브) 73.1%)")
    import json
    json.dump({"model":a.model,"n_ctrl":nc,"n_treat":nt,
               "sf_ott":round(cs,1),"sf_neutral":round(ts,1),"sf_delta":round(ts-cs,1),
               "sf_ott_ci":[round(clo,1),round(chi,1)],"sf_neutral_ci":[round(tlo,1),round(thi,1)],
               "cond_ott":round(cc,1),"cond_neutral":round(tc,1)},
              open(f"outputs/framing_exp_{a.model}.json","w"),ensure_ascii=False,indent=2)
    print(f"\n저장: outputs/framing_exp_{a.model}.json")
