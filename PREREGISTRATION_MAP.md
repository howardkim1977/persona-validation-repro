# Preregistration Correspondence Table

**Registration:** OSF `dfe2z` (https://osf.io/dfe2z), registered 2026-07-03.

> **[DRAFT — 저자 확인 필요]** 아래 "사전등록 항목" 열은 저장소 기록·작업 규칙을
> 근거로 재구성한 초안이다. 업로드 전에 OSF 등록 원문과 문구 단위로 대조하여
> 확정할 것.

## A. Preregistered elements → where reported

| Preregistered element | Paper location | Status |
|---|---|---|
| Primary model `gemini-3.5-flash` (thinking=low, top_p=1.0); comparison model EXAONE (open-weight, OpenAI-compatible endpoint) | Sec. III-C | As registered |
| Temperature 1.0 (main) / 0.7 (robustness) | Secs. III-D, IV-F | As registered |
| Bulk generation via Gemini Batch API (parameters unchanged) | Sec. III-D | As registered |
| Stratified allocation `n = clip(2×actual, 200, 600)` per sex-by-age cell (~8,000/model) | Sec. III-B | As registered |
| Format-violation regeneration, max 3 attempts | Sec. III-D | As registered |
| Conditional-item skip logic mirroring the survey | Sec. III-D | As registered |
| Ground reference: KISDI Korea Media Panel Survey, weighted estimates | Sec. III-A | As registered (terminology in paper: "reference estimates") |
| RQ1 overall agreement; RQ2 segment error; RQ3 small-sample calibration | Secs. IV-A, IV-B, IV-G | As registered |

## B. Post-hoc analyses (not preregistered; added during analysis/review)

| Analysis | Paper location | Reason added |
|---|---|---|
| 2025 item-set regeneration + reference-year swap | Sec. IV-E | Temporal-misalignment diagnosis |
| Wording-controlled paired framing regeneration | Sec. IV-D, Table 3 | Isolate item-framing cause |
| Temporal holdout (2024-learned correction → 2025) + out-of-time references | Sec. IV-G, Table 4 | Cross-wave transferability |
| Real-data-only estimators, calibration-size learning curve (1–30%), entire-cell holdout | Sec. IV-G, Table 5 | Bound calibration value against direct use of the calibration sample |
| Household-cluster split check | Secs. III-F, IV-G | Rule out within-household leakage |
| Teen-cell-excluded rerun of all headline metrics | Sec. IV-B, Appendix | Population-comparability sensitivity |
| Naive baselines (grand mean, prior wave) and demographic-only ablation | Secs. IV-H, IV-I, Table 6 | Baseline discipline |
| Design-based variance (Kish deff, household bootstrap), ICC / repeated passes | Secs. III-E, IV-J | Uncertainty and stability |
| Leave-one-item-out MAE, median AE, item-bootstrap correlation CIs | Secs. IV-A, IV-E | Single-item dominance check |
| Sampling-cap sensitivity (150–600) | Sec. III-B | Constant-choice robustness |

All post-hoc additions are diagnostic or conservative (they narrow, never
expand, the preregistered claims).
