# -*- coding: utf-8 -*-
"""본문에 인용된 보조 수치의 재현(패키지 루트에서 실행) → 시트 심사_보조수치.
(a) 합성 유튜브 이용률: 유효 페르소나 비가중 평균(2024, 2025)과 사후층화값(IV-D 의 93.9% 는 2025 문항셋 비가중값).
(b) 온도 1.0 대 0.7 의 사후층화 지표 비율 평균절대차(모델별, 이진 8지표; 점유율은 2024 만 10세 이상 실측).
(c) 요청당 평균 입력 문자 수(systemInstruction + contents 텍스트의 문자 수):
    순서 실험 고정순서 F1 1차 페이로드(2024 36문항, 서사 조건화)와 2025 배치 페이로드(1차 및 전체 라운드, 총량 포함).
(d) 5점 응답 스타일: 논문 IV-C 가 인용하는 값은 구성개념 8개의 사후층화 평균(Gemini 2.54, EXAONE 3.03,
    실측 2.83)이며, 원문항 24개 비가중 평균 2.45/3.05 는 단위가 다른 별개 통계로 함께 기록한다.
    최상점(5) 선택 비율과 1~5 분포도 원문항 기준이다.
(e) 이진 문항 '예' 선택률: 논문 IV-C 는 8개 지표의 사후층화 이용률 평균(Gemini 51.6%, EXAONE 57.5%,
    실측 55.9%)을 인용하며, 원문항 응답 합산 비율은 참고용으로 함께 기록한다."""
import glob, json
import numpy as np, pandas as pd
from rr_common import BIN, CON, CELL, SYN_FILES, load_real, load_syn, syn_cell_means, post_stratified_rate, write_sheets, Real
from items import ITEMS_BY_WAVE

rows = []
a_all = pd.read_csv("analysis_ready.csv", encoding="utf-8-sig")
def add(item, value, unit, paper, source):
    rows.append({"항목": item, "값": value, "단위": unit, "논문값": paper, "산식/출처": source})

# (a) 유튜브 이용률
real24 = load_real(2024, with_hid=False); R24 = Real(real24, BIN + CON)
# 조건부 문항은 그 문항 응답자만으로 셀 점유율을 계산한다
SH24 = {v: R24.cell_share(v=v) for v in BIN + CON}; share24 = R24.cell_share()
real25 = load_real(2025, with_hid=False); R25 = Real(real25)
SH25 = {v: R25.cell_share(v=v) for v in BIN}; share25 = R25.cell_share()
for yr, f, share in [(2024, "outputs/synthetic_recoded_gemini.csv", SH24), (2025, "outputs/synthetic_recoded_2025_gemini.csv", share25)]:
    s = load_syn(f); unw = s["유튜브_이용"].mean() * 100
    sh = share["유튜브_이용"] if isinstance(share, dict) and "유튜브_이용" in share else share
    ps = post_stratified_rate(sh, syn_cell_means(s, ["유튜브_이용"])["유튜브_이용"]) * 100
    add(f"Gemini {yr} 유튜브 이용률(유효 페르소나 비가중)", round(unw, 1), "%", "93.9 (IV-D, 2025 문항셋)" if yr == 2025 else "-", f"{f}, 유튜브_이용 단순평균 n={s['유튜브_이용'].notna().sum()}")
    add(f"Gemini {yr} 유튜브 이용률(사후층화)", round(ps, 1), "%", "-", f"{f}, 실측 {yr} 셀 점유율 사후층화")
    if yr == 2025:
        t = a_all[(a_all.YEAR == 2025)][["유튜브_이용", "WT"]].dropna()
        add("실측 2025 유튜브 이용률(가중, 전체 표본)", round(np.average(t["유튜브_이용"], weights=t["WT"]) * 100, 1), "%", "95.5 (IV-D)", "analysis_ready.csv 2025 전체(n=8,411), WT 가중; 만 10세 이상 표본에서는 " + f"{R25.overall_wmean('유튜브_이용') * 100:.1f}")

# (b) 온도 강건성: 사후층화 비율의 평균절대차
for m, f10, f07 in [("Gemini", "outputs/synthetic_recoded_gemini.csv", "outputs/synthetic_recoded_gemini_t07.csv"),
                    ("EXAONE", "outputs/synthetic_recoded_exaone.csv", "outputs/synthetic_recoded_exaone_t07.csv")]:
    c10 = syn_cell_means(load_syn(f10)); c07 = syn_cell_means(load_syn(f07))
    d = [abs(post_stratified_rate(SH24[v], c10[v]) - post_stratified_rate(SH24[v], c07[v])) * 100 for v in BIN]
    add(f"{m} 온도 1.0 대 0.7 사후층화 비율 평균절대차(이진 8지표)", round(float(np.mean(d)), 2), "%p", "0.5 (Gemini), 4.0 (EXAONE) (IV-F)",
        f"{f10} vs {f07}; 2024 만 10세 이상 실측 셀 점유율; 지표별 |차|: " + ", ".join(f"{v}={x:.1f}" for v, x in zip(BIN, d)))

# (c) 요청당 입력 문자 수
def payload_chars(pattern):
    n = 0; chars = 0
    for p in sorted(glob.glob(pattern)):
        for line in open(p, encoding="utf-8"):
            o = json.loads(line); n += 1
            chars += len(o["request"]["systemInstruction"]["parts"][0]["text"]) + len(o["request"]["contents"][0]["parts"][0]["text"])
    return n, chars
for label, pat, paper in [("순서 실험 F1 1차 페이로드(2024 문항셋) 요청당 평균 입력 문자", "logs/order_F1_r0c*.jsonl", "약 4,400 (III-D, 2024 요청 추정치)"),
                          ("2025 배치 1차 페이로드 요청당 평균 입력 문자", "logs/batch_w2025_r0c*.jsonl", "약 1,800 (III-D)"),
                          ("2025 배치 전체 라운드 페이로드 요청당 평균 입력 문자", "logs/batch_w2025_r*c*.jsonl", "약 1,800 (III-D)")]:
    n, chars = payload_chars(pat)
    add(label, round(chars / n), "문자", paper, f"{pat}: 요청 {n:,}건, 총 {chars / 1e6:.2f}M 문자")
    if "전체" in label:
        add("2025 배치 전체 라운드 페이로드 총 입력 문자", round(chars / 1e6, 2), "M 문자", "14.1M (III-D)", f"{pat}: 요청 {n:,}건")

# (d) 5점 문항 응답 스타일(원문항)
M_ITEMS = [f"p__m010{i:02d}" for i in range(1, 25)]
raw = {"Gemini": pd.read_csv("outputs/synthetic_responses.csv", encoding="utf-8-sig", low_memory=False),
       "EXAONE": pd.read_csv("outputs/synthetic_exaone.csv", encoding="utf-8-sig", low_memory=False)}
for m, d in raw.items():
    if "_error" in d: d = d[d["_error"].isna()]
    vals = d[M_ITEMS].to_numpy(float).ravel(); vals = vals[~np.isnan(vals)]
    dist = {k: (vals == k).mean() * 100 for k in [1, 2, 3, 4, 5]}
    add(f"{m} 5점 문항 최상점(5) 선택 비율", round(dist[5], 2), "%", "almost never (IV-C, Gemini)" if m == "Gemini" else "-",
        f"원문항 24개 응답 {len(vals):,}건; 분포 1~5 = " + " / ".join(f"{dist[k]:.1f}" for k in [1, 2, 3, 4, 5]) + f"; 상위 4-5 = {dist[4] + dist[5]:.1f}%")
    add(f"{m} 5점 문항 응답 평균(원문항 24개, 비가중)", round(float(vals.mean()), 2), "점", "-(논문 미인용; IV-C 는 구성개념 사후층화 평균을 쓴다)", "진단_응답스타일 의 5점_평균과 동일 산식")
for m, f in SYN_FILES.items():
    cm = syn_cell_means(load_syn(f), CON)
    add(f"{m} 구성개념 8개 사후층화 평균(5점)", round(float(np.mean([post_stratified_rate(SH24[v], cm[v]) for v in CON])), 3), "점",
        "2.54 (Gemini), 3.03 (EXAONE) (IV-C)", "구성개념 시트의 모델 열 8개 값의 평균과 동일")
cons = [R24.overall_wmean(v) for v in CON]
add("실측 2024 5점 기준값(8개 구성개념 가중평균의 평균, 만 10세 이상)", round(float(np.mean(cons)), 3), "점", "-", "analysis_ready.csv 2024 만 10세 이상, 구성개념별 WT 가중평균의 단순평균")
a_full = a_all[a_all.YEAR == 2024]
cons_full = []
for v in CON:
    t = a_full[[v, "WT"]].dropna(); cons_full.append(np.average(t[v], weights=t["WT"]))
add("실측 2024 5점 기준값(8개 구성개념 가중평균의 평균, 전체 표본)", round(float(np.mean(cons_full)), 3), "점", "2.83 (IV-C)", "analysis_ready.csv 2024 전체(n=8,693), 구성개념 시트의 실측_가중 8개 값의 평균")

# (e-1) 이진 '예' 선택률: 논문 IV-C 가 쓰는 사후층화 기준(실측과 같은 산식)
sv8 = [np.average(a_full[[v, "WT"]].dropna()[v], weights=a_full[[v, "WT"]].dropna()["WT"]) for v in BIN]
add("실측 2024 이진 '예' 선택률(8지표 가중 이용률의 평균, 전체 표본)", round(float(np.mean(sv8)), 3), "비율", "55.9% (IV-C)", "RQ1_전체일치도 의 실측_가중 8개 값의 평균")
for m, f in SYN_FILES.items():
    cm = syn_cell_means(load_syn(f), BIN)
    add(f"{m} 이진 '예' 선택률(8지표 사후층화 이용률의 평균)", round(float(np.mean([post_stratified_rate(SH24[v], cm[v]) for v in BIN])), 3), "비율",
        "51.6% (Gemini), 57.5% (EXAONE) (IV-C)", "RQ1_전체일치도 의 모델 열 8개 값의 평균과 동일; 진단_응답스타일 의 이진_예선택률_사후층화")

# (e) 이진 문항 '예' 선택률
bin_items = [c for c, (t, o) in ITEMS_BY_WAVE[2024].items() if set(o.keys()) == {1, 2}]
for m, d in raw.items():
    if "_error" in d: d = d[d["_error"].isna()]
    b8 = d[["p__d31002", "p__d26001", "p__d26075", "p__d26092", "p__d11001", "p__d22001", "p__d28001", "p__d29001"]].to_numpy(float).ravel(); b8 = b8[~np.isnan(b8)]
    ball = d[[c for c in bin_items if c in d.columns]].to_numpy(float).ravel(); ball = ball[~np.isnan(ball)]
    per_item = {c: float((d[c].dropna() == 1).mean()) for c in bin_items if c in d.columns}
    add(f"{m} 이진 '예' 선택률(8지표 원문항, 응답 합산)", round(float((b8 == 1).mean()), 3), "비율", "-(논문 미인용; 참고용 비가중 산식. 진단_응답스타일 의 이진_예선택률_비가중)", f"응답 {len(b8):,}건")
    add(f"{m} 이진 '예' 선택률(2024 문항셋의 2택 문항 {len(bin_items)}개 전체, 응답 합산)", round(float((ball == 1).mean()), 3), "비율", "-", f"응답 {len(ball):,}건; 문항: " + ", ".join(bin_items))
    add(f"{m} 이진 '예' 선택률(2택 문항 {len(bin_items)}개, 문항별 비율의 평균)", round(float(np.mean(list(per_item.values()))), 3), "비율", "-", "; ".join(f"{c}={v:.3f}" for c, v in per_item.items()))

df = pd.DataFrame(rows)
write_sheets({"심사_보조수치": df})
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
print(df[["항목", "값", "단위", "논문값"]].to_string(index=False))
