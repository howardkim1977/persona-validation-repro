# Preregistration Correspondence Table

**Registration:** OSF `dfe2z` (https://osf.io/dfe2z), registered 2026-07-03 (OSF timestamp 02:36 UTC). File timestamps show that the registration was submitted after the 2024 Gemini and EXAONE panels had been generated (2 July 22:25 and 3 July 02:01 KST) and after an initial overall and cell-level agreement computation (3 July 06:18 and 07:41 KST), and before the calibration, diagnostic, and temporal analyses were designed; the paper (Sec. III-H, Table 3) therefore labels the RQ1–RQ2 plan as registered rather than as strictly preregistered. The registration's own prior-knowledge statement (form field "Prior knowledge of the data": "The synthetic-persona responses have not yet been generated, and no comparison between the synthetic and observed distributions has been computed") was therefore inaccurate when filed; this table and the paper correct it. This table was last updated 2026-09-03. Section and table numbers refer to the September 2026 version of the manuscript; the paper's Table 3 reproduces the status classification below. Registration type: Secondary Data Preregistration. The
registration was under embargo until 2026-08-23, when the authors ended the
embargo early; it is now public, and every row below has been checked
word-by-word against the registration text.

**Title change.** The registration is titled "Validating Synthetic Personas for
Predicting Digital and AI Service Adoption: A Benchmark Against the Korea Media
Panel Survey." The manuscript title was later changed to
"Distributional Validity and Calibration of a Korean Synthetic Persona Panel for
Digital and AI Service Use: A Secondary-Data Validation Against the Korea Media
Panel Survey." The change narrows the claim ("benchmark"/"predicting adoption"
to "distributional validity"/"service use") and adds the calibration component;
the study, data, and design are unchanged. In the September 2026 revision the
title was shortened to "Distributional Validity of a Korean Synthetic Persona
Panel: Evidence from the Korea Media Panel Survey"; scope and design are
unchanged.

## Provenance of the registration timeline

The timeline stated above rests on the local modification times of the working
copy from which this package was assembled (macOS, `stat -f '%Sm'`, times in
KST, UTC+9) and on the run logs. The table gives, for the files that fix the
sequence, the SHA-256 of the archived copy (identical to the working copy) and
that local modification time. The modification times inside a downloaded
Zenodo/GitHub archive are the packaging time and are not evidence of the
sequence; the hashes identify the files, the times below are the evidence
carried by the working copy.

| File (package path) | SHA-256 | Local mtime (KST) |
|---|---|---|
| `code/map_persona.py` | `fc99b3a501a87f803cb5174e6f4b6f2e2ddee1a7cd3b0e222fadd527ad4fd482` | 2026-07-02 08:55:36 |
| `code/items.py` | `58714e5ed81307ef7d94d3243519eda043d03da8bdb8a678af6067abb634fe9d` | 2026-07-02 08:56:26 |
| `code/recode.py` | `e2b6ddee6e1def79a00d8d75760f5b273e88048ad33af2c9eca0602355fecc67` | 2026-07-02 08:56:26 |
| `outputs/synthetic_responses.csv` (Gemini 2024 main run) | `bc2c7ac2309b1043b425e2398fd64c8f3e4aa5bafa356677492ab0f87efe12c9` | 2026-07-02 22:25:02 |
| `outputs/synthetic_exaone.csv` (EXAONE 2024 main run) | `6f585672495742df00dff8f33365238bba1d52cf991427ef01b565e39253858f` | 2026-07-03 02:01:13 |
| `code/compare_validity.py` (first RQ1/RQ2 computation) | `e7a0650bcf351a61e5df6fb856680fb534dc64852f0847cfd75547da787eda77` | 2026-07-03 06:18:25 |
| `outputs/validity_RQ1_overall.csv` | `ad3e186a31d2ea145aaa672236f3268da960f40013ef62d4cdbf13e4ccf924e4` | 2026-07-03 06:18:26 |
| `code/analyze_extra.py` (cell-level table, constructs) | `6ca23800fd49a41fdec33e4cb550b201b27bd54dddfa2e80fd286e927664704a` | 2026-07-03 07:41:35 |
| `outputs/validity_RQ2_cells.csv` | `883ea58d84212abffa1c8101033421a1270a8370e4f0b9d4538b5c64e841dbbb` | 2026-07-03 07:41:35 |
| `outputs/validity_constructs.csv` | `1c22b82d25a40595fee35fc82995d7473c71994f3c14866bc5dd687ce9f7b57c` | 2026-07-03 07:41:35 |
| `code/build_paper_tables.py` (first workbook) | `61ba3fc634ae0782648ad87aa3c6d7e0e0e40d7f909cfba63812d682ce6e5480` | 2026-07-03 07:42:20 |
| `code/build_dual_tables.py` (2025 reference tables) | `72fd42705822b806b34b1cf35d302e2039fff87fde7df9748e64abfad8b4ec08` | 2026-07-03 08:00:01 |
| `outputs/synthetic_responses_t07.csv` (Gemini, temperature 0.7) | `15a25d61ec547adfad464abe32a85371f6cfdd854bc6d3202c99ac1e6f8ea74e` | 2026-07-03 08:35:46 |
| `outputs/synthetic_exaone_t07.csv` (EXAONE, temperature 0.7) | `61ade6e7214f5ed53c4d43426e5d43ecad4795d18a6b8ad11bdab37f7269815b` | 2026-07-03 11:23:10 |
| `outputs/synthetic_2025.csv` (Gemini 2025 run) | `8d2ffccb25b8c0c259e8f1f32568ba5be25908fba233754b674ec31e36322659` | 2026-07-03 11:55:10 |
| `outputs/synthetic_exaone_2025.csv` (EXAONE 2025 run) | `df103a5014c357f58a316d732952dba8cd3d78504471dc243c21a45b85ab957f` | 2026-07-03 14:26:15 |
| `code/generate.py` (last edited after the runs: `max_tokens` 4,096, recovery) | `758b0d6e84963c6c3d51cb1264a8dfcff9683f2568cb9e0e5eb0c60f0385188d` | 2026-07-04 22:43:14 |

The Nemotron-Personas-Korea source file (outside the package; SHA-256 in
`DATASET_HASHES.txt`) has local mtime 2026-07-02 18:49:29 KST (download time).

**Gemini Batch API job identifiers of the 2024 main run** (from
`logs/run_batch_full.log`; the log file itself was copied into the package on
2026-09-03, so its mtime is not informative). Round 1, nine sub-batches in
order: `batches/fa6f6zv7xa78l2080xtk5v6sey6b94apbeoy`,
`batches/q5k3tda139pdn6wzsqt7tlbulk76fek5023s`,
`batches/x7e167e9n03u7klaxixjpb5d9hsoxg6hxfph`,
`batches/w39m0fg4tqnyme7evxootru2hantm5beqrqy`,
`batches/z1nqteagbjc8cxuxzhmsv4jl37v36xigl5ae`,
`batches/b8kywj6oh40h54ta94psfimfu20tths28mz0`,
`batches/4mbonnm3z5wsors9th70ay8mi014sk0swxxl`,
`batches/qvb5nffmwfzldndumlbjzweerg5hu62ckmvn`,
`batches/pdwz3ifhop84i43skmbfg720zgvdsswc4vjd`; round 2 (66 resubmissions):
`batches/fbrrg0nw38550v3igovm2zycd418i2jw4awu`. These identifiers are recorded
in the Google account's batch job history with server-side creation times.

**Git history of the working repository.** The command
`git -C <working repo> log --since=2026-07-01 --until=2026-07-05 --format='%h %ci %s'`
returns no commits: the working repository was initialised after the runs, its
first commit being `5654014 2026-07-09 15:00:38 +0900 Initial commit: 합성 페르소나
예측 타당성 검증 재현성 패키지`, and the package repository's first commit is
`30599e9 2026-07-16 22:19:52 +0900`. No version-control timestamps exist for
2-4 July 2026; the file modification times and the batch job identifiers above
are the only local records of the sequence.

## A. Preregistered elements → where reported

| Preregistered element | Paper location | Status |
|---|---|---|
| Primary model `gemini-3.5-flash` (thinking=low, top_p=1.0); comparison model EXAONE (open-weight, OpenAI-compatible endpoint) | Sec. III-C | As registered |
| Temperature 1.0 (main) / 0.7 (robustness) | Secs. III-D, IV-F | As registered |
| Bulk generation via Gemini Batch API (parameters unchanged) | Sec. III-D | As registered |
| Stratified allocation `n = clip(2×actual, 200, 600)` per sex-by-age cell (~8,000/model) | Sec. III-B | As registered |
| Format-violation regeneration, max 3 attempts | Sec. III-D | As registered |
| Conditional-item skip logic mirroring the survey | Sec. III-D | As registered for the generative-AI sub-items; extended post hoc (v1.20) to the YouTube and short-form items, which the survey asks only of OTT users and which the archived runs had answered unconditionally (see PROTOCOL.md) |
| Ground reference: KISDI Korea Media Panel Survey, weighted estimates | Sec. III-A | As registered (terminology in paper: "reference estimates") |
| RQ1: do aggregated synthetic responses reproduce population-level distributions? | Sec. IV-A | As registered |
| RQ2: does correspondence vary across respondent groups, item types, and model/generation settings? | Secs. IV-B, IV-F | Partly — respondent groups and generation settings as registered; item-type contrast deviates, see B |
| H1 agreement measured against a chance/null reference | Secs. IV-H, Table 9 | Deviation — see B |
| H2 subgroup agreement by sex-by-age cell and by item type | Sec. IV-B | Sex-by-age cells as registered; item-type contrast deviates, see B |
| Agreement metrics: total variation distance (primary), Jensen–Shannon divergence, Pearson/rank correlation | Secs. III-E, IV-A | Deviation — see B |
| H2 modelled by mixed-effects regression of agreement on cell size, age group, item type | — | Not performed — see B |

## B. Deviations from the registered plan

| Registered | Reported instead | Rationale |
|---|---|---|
| Total variation distance as the primary agreement measure | Mean absolute error (MAE) as the primary measure, with cosine similarity, KL and Jensen–Shannon divergences, and item-mean Pearson correlation | The item set is dominated by binary use/non-use indicators, for which MAE is directly interpretable in percentage points and is the unit in which the paper's claims and the calibration results are stated. JS divergence and Pearson correlation are reported as registered; TVD is not reported separately. |
| Chance/null reference: uniform or marginal-permutation baseline | Grand-mean baseline (overall weighted rate for every cell) and prior-wave baseline (2023 real cell rates) | Naive real-data baselines are a stricter test than a uniform or permutation reference: they ask whether the synthetic panel beats trivial use of the real data, not merely whether it beats chance. The paper reports that the uncorrected panel fails this stricter test. |
| Mixed-effects regression of cell- and item-level agreement on cell size, age group, and item type, with random intercepts for item | Five-axis segment decomposition of cell error (age, sex, region, education, employment) plus leave-one-item-out and item-bootstrap checks | The registered regression was not run. The five-axis decomposition addresses the same question (whether error concentrates in particular groups) descriptively; no inferential model of agreement was fitted. |
| Item-type contrasts: binary vs. multi-category items, and general digital vs. AI items | Binary indicators vs. 5-point constructs (Secs. IV-A, IV-B; Table 15); the three multi-category AI items (awareness, most-used service, purpose of use) were not analysed | The multi-category items have no persona-side analogue with comparable option sets; the binary/construct contrast covers the registered intent of comparing item types |
| Robustness summaries: correlation and mean absolute difference of item-level agreement across settings (temperature, model) | Mean absolute differences and paired design-based bootstrap CIs (Sec. IV-F); cross-setting correlations not reported | The paired bootstrap answers the registered question more directly; correlations across eight items would be uninformative |
| Eight age categories for cell-level comparison | Seven decade bands (teens to 70s and over); respondents under 10 (weighted share 1.1%) are excluded from all cell-based analyses because no persona is under 19 (Sec. III-B) | The persona source has no under-10 records; the exclusion moves indicator rates by at most 0.7 pp |

## C. Analyses not preregistered (added during analysis and review)

| Analysis | Paper location | Reason added |
|---|---|---|
| **RQ3 (calibration) in its entirety** — the registration states only RQ1 and RQ2; no calibration research question, hypothesis, or analysis plan was registered | Secs. III-F, IV-G; Tables 7–8 | Added after the raw comparison showed large, structured (not random) error, to test whether that structure is correctable |
| Structural bias signatures (age slopes of the signed error, response-style level and anchoring) | Sec. IV-C, Fig. 4, Tables 12–13 | Diagnose the structure of the error before calibration |
| 2025 item-set regeneration + reference-year swap | Sec. IV-E | Temporal-misalignment diagnosis |
| Wording-controlled paired framing regeneration | Sec. IV-D, Table 6 | Isolate item-framing cause |
| Temporal holdout (2024-learned correction → 2025) + out-of-time references | Sec. IV-G, Table 7 | Cross-wave transferability |
| Real-data-only estimators, calibration-size learning curve (1–30%), entire-cell holdout | Sec. IV-G, Table 8 | Bound calibration value against direct use of the calibration sample |
| Household-cluster split check | Secs. III-F, IV-G | Rule out within-household leakage |
| Teen-cell-excluded rerun of all headline metrics | Sec. IV-B, Appendix | Population-comparability sensitivity |
| Demographic-only ablation | Sec. IV-I | Baseline discipline |
| Design-based variance (Kish deff, household bootstrap), ICC / repeated passes | Secs. III-E, IV-J | Uncertainty and stability |
| Leave-one-item-out MAE, median AE, item-bootstrap correlation CIs | Secs. IV-A, IV-E | Single-item dominance check |
| Sampling-cap sensitivity (150–600) | Sec. III-B | Constant-choice robustness |
| Nested correction-form selection, all candidate forms, partially pooled (EB) estimators, learning curve at 1–30% with win shares, 19-year-old comparison, construct correlation structure, paired model bootstrap, hierarchical bootstrap | Secs. III-F, IV-A, IV-B, IV-G, IV-J; Tables 7–8, 14–15 | Added after the initial analysis |
| Randomized-order regeneration (1,144-persona subsample; three fixed-order responses + one random-order response) | Sec. IV-K | Added after the initial analysis; bounds the item-order component of context effects |

Most additions in Section C test robustness or bound the paper's claims. RQ3 is a
substantive exploratory extension that also produces a positive calibration
result; it is reported alongside real-data-only estimators that bound what the
calibration actually buys.