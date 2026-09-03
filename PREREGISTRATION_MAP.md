# Preregistration Correspondence Table

**Registration:** OSF `dfe2z` (https://osf.io/dfe2z), registered 2026-07-03,
updated 2026-07-12. Section and table numbers refer to the revised manuscript (September 2026); the paper's Table 3 reproduces the status classification below. Registration type: Secondary Data Preregistration. The
registration was under embargo until 2026-08-23, when the authors ended the
embargo early; it is now public, and every row below has been checked
word-by-word against the registration text.

**Title change.** The registration is titled "Validating Synthetic Personas for
Predicting Digital and AI Service Adoption: A Benchmark Against the Korea Media
Panel Survey." The manuscript title was revised during review to
"Distributional Validity and Calibration of a Korean Synthetic Persona Panel for
Digital and AI Service Use: A Secondary-Data Validation Against the Korea Media
Panel Survey." The change narrows the claim ("benchmark"/"predicting adoption"
to "distributional validity"/"service use") and adds the calibration component;
the study, data, and design are unchanged.

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
| RQ1: do aggregated synthetic responses reproduce population-level distributions? | Sec. IV-A | As registered |
| RQ2: does correspondence vary across respondent groups, item types, and model/generation settings? | Secs. IV-B, IV-F | As registered |
| H1 agreement measured against a chance/null reference | Secs. IV-H, Table 9 | Deviation — see C |
| H2 subgroup agreement by sex-by-age cell and by item type | Sec. IV-B | As registered |
| Agreement metrics: total variation distance (primary), Jensen–Shannon divergence, Pearson/rank correlation | Secs. III-E, IV-A | Deviation — see C |
| H2 modelled by mixed-effects regression of agreement on cell size, age group, item type | — | Not performed — see C |

## B. Deviations from the registered plan

| Registered | Reported instead | Rationale |
|---|---|---|
| Total variation distance as the primary agreement measure | Mean absolute error (MAE) as the primary measure, with cosine similarity, KL and Jensen–Shannon divergences, and item-mean Pearson correlation | The item set is dominated by binary use/non-use indicators, for which MAE is directly interpretable in percentage points and is the unit in which the paper's claims and the calibration results are stated. JS divergence and Pearson correlation are reported as registered; TVD is not reported separately. |
| Chance/null reference: uniform or marginal-permutation baseline | Grand-mean baseline (overall weighted rate for every cell) and prior-wave baseline (2023 real cell rates) | Naive real-data baselines are a stricter test than a uniform or permutation reference: they ask whether the synthetic panel beats trivial use of the real data, not merely whether it beats chance. The paper reports that the uncorrected panel fails this stricter test. |
| Mixed-effects regression of cell- and item-level agreement on cell size, age group, and item type, with random intercepts for item | Five-axis segment decomposition of cell error (age, sex, region, education, household type) plus leave-one-item-out and item-bootstrap checks | The registered regression was not run. The five-axis decomposition addresses the same question (whether error concentrates in particular groups) descriptively; no inferential model of agreement was fitted. |

## C. Analyses not preregistered (added during analysis and review)

| Analysis | Paper location | Reason added |
|---|---|---|
| **RQ3 (calibration) in its entirety** — the registration states only RQ1 and RQ2; no calibration research question, hypothesis, or analysis plan was registered | Secs. III-F, IV-G; Tables 7–8 | Added after the raw comparison showed large, structured (not random) error, to test whether that structure is correctable |
| 2025 item-set regeneration + reference-year swap | Sec. IV-E | Temporal-misalignment diagnosis |
| Wording-controlled paired framing regeneration | Sec. IV-D, Table 9 | Isolate item-framing cause |
| Temporal holdout (2024-learned correction → 2025) + out-of-time references | Sec. IV-G, Table 7 | Cross-wave transferability |
| Real-data-only estimators, calibration-size learning curve (1–30%), entire-cell holdout | Sec. IV-G, Table 8 | Bound calibration value against direct use of the calibration sample |
| Household-cluster split check | Secs. III-F, IV-G | Rule out within-household leakage |
| Teen-cell-excluded rerun of all headline metrics | Sec. IV-B, Appendix | Population-comparability sensitivity |
| Demographic-only ablation | Sec. IV-I | Baseline discipline |
| Design-based variance (Kish deff, household bootstrap), ICC / repeated passes | Secs. III-E, IV-J | Uncertainty and stability |
| Leave-one-item-out MAE, median AE, item-bootstrap correlation CIs | Secs. IV-A, IV-E | Single-item dominance check |
| Sampling-cap sensitivity (150–600) | Sec. III-B | Constant-choice robustness |
| Nested correction-form selection, all candidate forms, partially pooled (EB) estimators, learning curve at 1–30% with win shares, 19-year-old comparison, construct correlation structure, paired model bootstrap, hierarchical bootstrap | Secs. III-F, IV-A, IV-B, IV-G, IV-J; Tables 7–8, 13–14 | Added in the first-round revision (reviewer requests) |
| Randomized-order regeneration (1,144-persona subsample; three fixed-order responses + one random-order response) | Sec. IV-K | Added in the first-round revision (reviewer request): bounds the item-order component of context effects |

All additions in Section C are diagnostic or conservative: each one narrows,
rather than expands, the claims the paper makes. RQ3 is the one substantive
addition, and it is reported alongside real-data-only estimators that bound
what the calibration actually buys.
