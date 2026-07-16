# Prompt & Generation Protocol

This document specifies the full conditioning and generation protocol. The
`logs/batch_*.jsonl` files contain the exact request payloads sent to the
Gemini Batch API and can be used to verify every element below byte-for-byte.

## 1. Persona block

Each sampled Nemotron-Personas-Korea record is rendered as a first-person
persona block. Structured attributes are mapped to Korean survey categories
(`code/map_persona.py`), then concatenated with the record's narrative fields
(life background, hobbies, cultural/media orientation). Template
(`code/generate.py::persona_description`):

```
성별 {gender}, 연령 {age band}, 학력 {school}, 개인 월평균 소득 {income},
거주지 {area}, 직업 {job}, {persona narrative fields}
```

The demographic-only ablation condition uses the same template with all
narrative fields removed (sex and age only).

## 2. System instruction (verbatim)

```
당신은 다음 특성을 가진 한국의 한 개인입니다: {persona}.
이 인물의 입장에서 일관되게, 실제 사람처럼 솔직하게 설문에 응답하십시오.
각 문항은 제시된 보기 번호 중 하나로만 답합니다.
```

## 3. User prompt (survey; verbatim template)

```
다음 문항에 답해 주십시오. 각 문항마다 보기 번호(숫자) 하나만 고릅니다.

[{item code}] {item text — original KISDI wording}
  보기: {k=v / k=v / ...}
... (all items in the wave's item set)

반드시 아래 JSON 형식으로만 출력하십시오. 설명·여는말 없이 JSON 객체 하나만 출력합니다.
{"문항코드": 보기번호, ...}
예: {"p__d31002": 1, "p__d31001": 3}
```

Item text and option sets are defined in `code/items.py` (codebook
P_codebook_v32): 36 items for the 2024 wave, 12 items for the 2025 wave. The
framing-experiment treatment variant replaces only the short-form item
(`p__d26092`) wording — removing "OTT" and naming the venues (YouTube Shorts,
Instagram Reels, TikTok) — with everything else identical
(`code/framing_experiment.py`).

## 4. Output contract, skip logic, retries

- **Output**: a single JSON object `{item_code: option_number}`; no prose.
- **Validation** (`code/generate.py::validate`): missing item, out-of-range
  code, or non-integer → the persona's entire response is regenerated, at most
  3 attempts; personas still failing are excluded (per-cell exclusion rates in
  `outputs/failure_rates_by_cell.csv`).
- **Conditional skip** (`code/generate.py::conditional_skips`): child items are
  omitted when the parent response indicates non-use (e.g., AI sub-items are
  asked only of AI users), mirroring the original survey's skip logic.
- **Rate limits**: 429/RESOURCE_EXHAUSTED retried with exponential backoff
  (does not consume regeneration attempts).

## 5. Models, endpoints, sampling parameters

| | Primary | Comparison |
|---|---|---|
| Model | `gemini-3.5-flash` | `K-EXAONE-236B-A23B` (LG AI Research) |
| Access | Google Gemini **Batch API**, sequential sub-batches ≤1,000 | FriendliAI serverless, OpenAI-compatible endpoint |
| Temperature | 1.0 (main) / 0.7 (robustness) | 1.0 (main) / 0.7 (robustness) |
| top_p | 1.0 | 1.0 |
| Reasoning | `thinkingLevel: low` | thinking disabled via chat-template argument |
| Concurrency | batch | ≤8 workers (higher settings truncated responses) |
| Response format | `responseMimeType: application/json` | JSON instruction in prompt |
| Serving window | July 2026 | July 2026 |
| Knowledge cutoff | January 2025 (documented) | undisclosed |

Credentials are injected via environment variables only (`GEMINI_API_KEY`,
`EXAONE_BASE_URL`, `EXAONE_API_KEY`); no keys appear in code or logs.

## 6. Sampling design

Sex-by-age stratified sampling from Nemotron-Personas-Korea with per-cell
allocation `n = clip(2 × actual cell count, 200, 600)`, uniform random with
replacement within cells, seed 42 (`numpy.random.default_rng`). The exact
source file is identified by SHA-256 in `DATASET_HASHES.txt`; re-running
`code/generate.py::sample_personas` with that file and seed reproduces the
identical persona selection.
