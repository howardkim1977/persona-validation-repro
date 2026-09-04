# Reproducibility Package

**Paper:** Distributional Validity of a Korean Synthetic Persona Panel: Evidence
from the Korea Media Panel Survey (IEEE Access, under review; earlier working
title: "Distributional Validity and Calibration of a Korean Synthetic Persona
Panel for Digital and AI Service Use: A Secondary-Data Validation Against the
Korea Media Panel Survey")

**Preprint:** arXiv:2608.28615, https://doi.org/10.48550/arXiv.2608.28615;
SocArXiv, https://doi.org/10.31235/osf.io/zb3w2_v1

**Archived package:** Zenodo — v1.16 (September 2026) https://doi.org/10.5281/zenodo.22306392;
v1.15 (September 2026) https://doi.org/10.5281/zenodo.22305839;
v1.14 (September 2026) https://doi.org/10.5281/zenodo.22305208;
v1.13 (September 2026) https://doi.org/10.5281/zenodo.22304928;
v1.12 (September 2026) https://doi.org/10.5281/zenodo.22304310;
v1.11 (September 2026) https://doi.org/10.5281/zenodo.22288893;
v1.10 (September 2026) https://doi.org/10.5281/zenodo.22284555;
v1.9 (September 2026) https://doi.org/10.5281/zenodo.22284201;
v1.8 (September 2026) https://doi.org/10.5281/zenodo.22282752;
v1.7 (September 2026) https://doi.org/10.5281/zenodo.22281821;
v1.6 (September 2026) https://doi.org/10.5281/zenodo.22280558;
v1.5 (September 2026) https://doi.org/10.5281/zenodo.22278987;
v1.4 (September 2026) https://doi.org/10.5281/zenodo.22276215;
v1.3 (September 2026) https://doi.org/10.5281/zenodo.22275444;
v1.2 (September 2026) https://doi.org/10.5281/zenodo.22274662;
v1.1 (September 2026) https://doi.org/10.5281/zenodo.22270829;
v1.0 (July 2026) https://doi.org/10.5281/zenodo.21397425;
all versions https://doi.org/10.5281/zenodo.21397424
(the README inside an archived version lists the DOIs of earlier versions only, because each
version DOI is minted after its GitHub release; the version's own DOI is in its Zenodo metadata)

**Preregistration:** OSF registration `dfe2z` (https://osf.io/dfe2z; public since 2026-08-23) — see
`PREREGISTRATION_MAP.md` for the item-by-item correspondence between the
registration and the reported analyses.

## Contents

| Path | Contents |
|---|---|
| `code/` | All generation, recoding, analysis, calibration, and figure scripts (Python) |
| `outputs/fig7_decision_flow.pdf` | The compiled decision flowchart (Fig. 8), so the package is complete without a TeX installation |
| `outputs/` | Raw synthetic responses of all full-panel runs, recoded response files, aggregate results workbook (`validity_results.xlsx`, 70 sheets), per-cell exclusion rates (`failure_rates_by_cell.csv`), the wording experiment's arm-level results (`framing_exp_*.json`; per-persona pairing was not retained, see `PROTOCOL.md`), the segment attributes of every sampled persona (`sampled_personas_2024.csv`, `sampled_personas_2025.csv`; see "Persona attributes without the 4.1 GB source"), the console-transcribed CSVs behind three sheets (`m1_variance_*.csv`, `m2_ablation.csv`), and five pre-run check files (see "Development artifacts") |
| `logs/` | Gemini Batch API request payloads exactly as sent (`batch_w2025_*.jsonl`: 2025 run; `batch_w2024_*.jsonl`: demographic-only 2024 ablation run, see `PROTOCOL.md` §4a; `order_*.jsonl` and `order_exp_gemini_R1_orders.json`: randomized-order experiment) and the console logs of every generation run (`run_*.log`, `recover_*.log`, `framing_*.log`, `order_exp_gemini.log`) |
| `PROTOCOL.md` | Prompt protocol: persona block construction, system/user templates (verbatim), JSON output contract, skip logic, retry rules, model identifiers/endpoints/serving window |
| `DATASET_HASHES.txt` | SHA-256 of the exact Nemotron-Personas-Korea file used, plus the sampling seed |
| `MANIFEST.sha256` | SHA-256 of every file in this package |
| `quickstart.py` | Verifies the manifest, prints the headline tables, renders Figs. 1-7 (see "Quick start") |
| `rebuild_manifest.py` | Rewrites `MANIFEST.sha256` (no argument) or verifies it without rewriting (`--check`: lists mismatched, missing, and unlisted files; exit code 1 if any) |

## What is *not* included, and why

- **KISDI Korea Media Panel Survey microdata** (`analysis_ready.csv`,
  `PanelData_*.csv`): access-restricted. Apply at the KISDI Media Statistics
  Portal (https://stat.kisdi.re.kr); after approval, `code/recode.py` documents
  the exact recoding from the raw KISDI file to the analysis schema used here.
  All analyses that require real data read `analysis_ready.csv` (column schema
  in the table below). Scripts that resample by
  household or use exact ages additionally read the raw KISDI individual file
  at the hard-coded path `private/PanelData_20260701.csv` (columns `OPID`,
  `hid`, `YEAR`, `p__age1`): `design_variance.py`, `rq3_realonly.py`,
  `rr_teen19.py`, and every `rr_*.py` script that calls
  `rr_common.load_real()` with household identifiers (`rr_paired_bootstrap.py`,
  `rr_calibration_details.py`, `rr_calibration_forms_extended.py`,
  `rr_eb_curve.py`, `rr_learning_curve.py`, `rr_dpd_supplements.py`,
  `rr_teen_nested.py`, `rr_hier_bootstrap.py`, `rr_order_analysis.py`).
  Without that file these scripts stop at the read step.
- **API keys**: all scripts read credentials from environment variables
  (`GEMINI_API_KEY`, `EXAONE_*`); none are stored in code.
- **Nemotron-Personas-Korea** (~4.1 GB): publicly available on Hugging Face
  (`nvidia/Nemotron-Personas-Korea`); verify the exact file with
  `DATASET_HASHES.txt`.

### `analysis_ready.csv` schema

One row per respondent and wave (2023: 9,757; 2024: 8,693, of whom 8,675 are aged 10 and
over; 2025: 8,411), UTF-8 with BOM, columns in this order. It is produced from the raw KISDI
file by `code/recode.py`'s counterpart on the survey side (the same recoding rules; see the
comments in `code/recode.py`). Columns marked "not used" are carried but read by no archived
script.

| Column | Type | Coding | Waves |
|---|---|---|---|
| `YEAR` | int | survey wave (2023, 2024, 2025) | all |
| `OPID` | int | KISDI person identifier (join key to `hid` in the raw file) | all |
| `WT` | float | person weight (2024 range 0.054 to 8.70) | all |
| `성별` | str | `남성`, `여성` | all |
| `연령대` | str | `10세미만`, `10대`, `20대`, `30대`, `40대`, `50대`, `60대`, `70대이상` | all |
| `학력` | str | `미취학`, `초졸이하`, `중졸이하`, `고졸이하`, `대졸이하`, `대학원이상` | all |
| `소득` | str | personal monthly income band, eight labels from `소득없음` to `500만이상` (not used) | all |
| `지역` | int | province code 1-17 (`AREA` dictionary in `code/rq2_region.py` and `code/generate.py`) | all |
| `직업유무` | str | `유직`, `무직` | all |
| `무직구분` | str | for `무직` only: `학생`, `전업주부`, `군인`, `무직/기타` (not used) | all |
| `AI_인지` | float | generative-AI awareness, codes 1-4 (not used) | 2024, 2025 |
| `AI_이용여부` | float | 1 = uses generative AI, 0 = does not (binary indicator) | 2024, 2025 |
| `AI_주이용서비스`, `AI_이용목적` | float | multi-category codes, AI users only (not analysed) | 2024, 2025 |
| `AI_유료이용` | float | 1/0, AI users only (not analysed) | 2024, 2025 |
| `챗봇_이용여부_2023` | float | 1/0, 2023 chatbot item (not analysed) | 2023 |
| `혁신성_기능`, `혁신성_쾌락`, `혁신성_사회`, `혁신성_인지` | float | innovativeness constructs, mean of four 5-point items each (1-5) | 2024 |
| `수용_성과기대`, `수용_노력기대`, `수용_사회영향`, `수용_촉진조건` | float | UTAUT acceptance constructs, mean of two 5-point items each (1-5) | 2024 |
| `OTT_이용`, `SNS_이용`, `메신저_이용`, `메타버스_이용`, `콘텐츠구독_이용` | int | 1 = used, 0 = not used (binary indicators) | all |
| `유튜브_이용` | float | 1/0; missing for respondents not asked the module (2024: 7,362 answered) | all |
| `숏폼_이용` | float | 1/0; same module as `유튜브_이용` | 2024, 2025 |

The eight binary indicators used throughout are `AI_이용여부`, `OTT_이용`, `유튜브_이용`,
`숏폼_이용`, `SNS_이용`, `메신저_이용`, `메타버스_이용`, `콘텐츠구독_이용` (`BIN` in
`code/rr_common.py`); the eight constructs are the `혁신성_*` and `수용_*` columns (`CON`).
The synthetic recoded files (`outputs/synthetic_recoded_*.csv`, written by `code/recode.py`)
carry `_model`, `_wave`, `성별`, `연령대`, the five `AI_*` columns, the eight constructs, and
the seven media indicators, with no `WT`.

### Persona attributes without the 4.1 GB source

`outputs/sampled_personas_2024.csv` and `outputs/sampled_personas_2025.csv` are written by
`code/rr_dump_sampled_personas.py`, which re-runs `code/generate.py::sample_personas` with
the fixed seed exactly as `rq2_expand.py`, `rq2_region.py`, and section 6 of
`sensitivity_teen_excluded.py` do. Each row is one sampled persona in draw order: `_idx`
(identical to `_idx` in the raw response files), `uuid`, the raw Nemotron fields `sex`,
`age`, `province`, `education_level`, `occupation` (recovered verbatim from the first line of
the persona block), the assigned cell (`성별` label, `연령대` code 1-8, `연령대_라벨`), and the
`map_persona` mappings `시도` (full province name) and `교육수준`. Rows: 8,168 for 2024
(478 + 490 + 12 × 600) and 7,938 for 2025 (382 + 356 + 12 × 600); the cell sequence is
identical to the `성별`/`연령대` columns of `outputs/synthetic_responses.csv` and
`outputs/synthetic_2025.csv`. Sampling is with replacement, so 8,097 and 7,885 distinct
`uuid` values appear. The three axis scripts above call `sample_personas` and therefore
need the source file; their `idx2seg`/`idx2sido` dictionaries can instead be built from these
CSVs, keyed by `_idx`, with `교육수준` passed through `EDU_MAP`, `occupation` through `emp()`,
and `시도` through `FULL2SHORT`. The scripts themselves are archived unchanged.

## Reproduction map (paper table/figure → script → workbook sheet)

Numbering follows the September 2026 version of the manuscript. Scripts are run from the
package root (`python3 code/<script>.py`) with `analysis_ready.csv` (and, where noted,
`private/PanelData_20260701.csv` or `nemotron_personas_korea.csv`) placed beside `code/`.

| Paper item | Script | Workbook sheet |
|---|---|---|
| Table 1 (model identifiers) | `PROTOCOL.md` §5 | — |
| Table 2 (format failures) | `rr_failure_cost.py` | `심사_형식실패`, `심사_형식실패_셀별`, `심사_생성규모` |
| Table 3 (analysis status) | `PREREGISTRATION_MAP.md` | — |
| Table 4 (RQ1 metrics), paired model comparison, Spearman | `compare_validity.py` (first RQ1 pass, `outputs/validity_RQ1_overall.csv`), `rq1_metrics.py`, `rr_paired_bootstrap.py` | `RQ1_전체일치도`, `RQ1_지표종합`, `심사_짝부트스트랩`, `심사_상관_Spearman`, `심사_상관_구성개념` |
| Construct means (Sec. IV-A, Fig. 3) and cell table | `analyze_extra.py` (`outputs/validity_constructs.csv`, `outputs/validity_RQ2_cells.csv`) | `구성개념`, `RQ2_셀별상세` |
| Workbook skeleton | `build_paper_tables.py` (creates the workbook from the three `outputs/validity_*.csv` files; `요약` holds transcribed headline values) | `개요`, `요약`, `RQ1_전체일치도`, `RQ2_변수별요약`, `RQ2_셀별상세`, `구성개념` |
| Table 5 (RQ2 axes, signed-error range and complements) | `rq2_expand.py`, `rq2_region.py`, `rr_dpd_supplements.py` | `RQ2_축별MAE`, `RQ2_지역축`, `RQ2_집단편향_Gemini`, `RQ2_집단편향_EXAONE`, `심사_집단오차지표`, `심사_집단오차_지표별` |
| 19-year-old comparison (Sec. IV-B) | `rr_teen19.py` | `심사_10대_19세비교` |
| Sec. IV-C bias signatures (Figs. 4 and 5) | `diagnose_bias.py` | `진단_숏폼연령`, `진단_유튜브숏폼일관성`, `진단_연령경사오차`; `진단_응답스타일` (transcribed, see "Sheets without a producing script") |
| Table 6 (framing experiment) | `framing_experiment.py` (arm-level JSON), `rr_framing_tests.py` | `진단_프레이밍통제` (transcribed from the JSON), `심사_프레이밍검정` |
| Sec. IV-E temporal mismatch (Fig. 6) | `build_dual_tables.py`, `rq1_metrics.py` | `RQ1_정답지2024`, `RQ1_정답지2025`, `정답지차수_효과`, `실측_연도변화`, `RQ1_지표종합`; `RQ1_2025문항셋` (see "Sheets without a producing script") |
| Table 7 (calibration by form; temporal holdout) | `rq3_calibration.py` (single split, superseded by the 200-split estimates), `rq_uncertainty.py`, `rr_calibration_details.py`, `rr_calibration_forms_extended.py` | `RQ3_보정_단일분할`, `RQ3_보정`, `심사_보정형태민감도`, `RQ3_시점홀드아웃`, `심사_보정형태_시점홀드아웃` |
| Table 8 (learning curve vs. real-only; EB shrinkage; entire-cell holdout) | `rq3_realonly.py`, `rr_calibration_forms_extended.py`, `rr_learning_curve.py`, `rr_eb_curve.py` | `RQ3_실측단독_학습곡선`, `RQ3_셀홀드아웃`, `심사_보정형태_학습곡선`, `심사_학습곡선_정밀`, `심사_EB풀링곡선`, `심사_보정형태_셀홀드아웃` |
| Table 9 (baselines, ablation) | `rq3_temporal_baseline.py`, `rr_baselines_common6.py`, `sensitivity_teen_excluded.py`, demographic-only run of `generate.py` (`--conditioning demographic`) | `베이스라인_공통6`, `베이스라인_공통6_보정`, `RQ3_시점홀드아웃`, `십대제외_베이스라인`, `M2_ablation` (transcribed from `outputs/m2_ablation.csv`) |
| Table 10 (randomized-order experiment, Sec. IV-K) | `order_experiment.py`, `rr_order_analysis.py` | `심사_순서실험_지표`, `심사_순서실험_MAE`, `심사_순서실험_구성개념` |
| Table 11 (teen-excluded sensitivity) | `sensitivity_teen_excluded.py`, `rr_teen_nested.py` | `십대제외_RQ1`, `십대제외_RQ2`, `십대제외_RQ3보정`, `십대제외_시점홀드아웃`, `십대제외_베이스라인`, `십대제외_추가축`, `심사_십대제외_보정형태`; `RQ2_십대제외강건성` (derived, see below) |
| Tables 12-13 (signed error by age band) | `rr_age_band_errors.py` (survey: weighted band rate on the age-10-and-over sample; synthetic: unweighted pooling of the two sex cells; this rule reproduces all 112 printed integers, the post-stratified alternative is given alongside) | `심사_연령대별_부호오차` |
| Table 14 (calibration coefficients, residuals) | `rr_calibration_details.py` | `심사_보정계수` |
| Table 15 (construct correlation structure) | `rr_construct_corr.py` | `심사_구성개념_상관요약`, `심사_구성개념_상관행렬` |
| Hierarchical bootstrap (Sec. IV-J) | `rr_hier_bootstrap.py`, `rr_order_analysis.py` | `심사_계층부트스트랩_EXAONE`, `심사_계층부트스트랩_Gemini` |
| Design-based CIs (Kish deff, household bootstrap) | `design_variance.py` | `설계기반_분산` |
| Sampling-cap sensitivity (Sec. III-B) | `sensitivity_sample.py` | `민감도_표본cap` |
| Item-bootstrap correlation CIs (Sec. IV-A) | `rr_item_bootstrap.py` | `심사_문항부트스트랩` |
| Median absolute error and leave-one-item-out MAE (Secs. IV-A, IV-E) | `rr_item_supplements.py` | `심사_문항보조통계` |
| Response stability (ICC, repeated passes) | `m1_variance.py` (writes `outputs/m1_variance_*.csv`), second and third EXAONE passes of `generate.py` with `recover_k2.py`, `recover_k23.py` | `M1_분산_Gemini`, `M1_분산_EXAONE`, `복수응답_K3` (transcribed, see below) |
| Auxiliary numbers quoted in the text (Secs. III-D, IV-C, IV-D, IV-F) | `rr_misc_numbers.py` | `심사_보조수치` |
| Persona sampling and generation | `generate.py` (`sample_personas`, live and batch modes), `map_persona.py`, `items.py`, `recode.py`; `rr_dump_sampled_personas.py` (segment attributes of the sampled personas) | none (files `outputs/synthetic_*.csv`, `outputs/sampled_personas_*.csv`) |
| Figures (all) | `render_figures.py` (values transcribed from the sheets listed in the figure table as literals); decision flowchart `fig7_decision_flow.tex` (TikZ) | see the figure table |

### Figure files

| File (`paper/figures/`, written by `quickstart.py`) | Paper figure | Source sheets |
|---|---|---|
| `fig0_framework` | Fig. 1 | schematic (no data) |
| `fig1_rq1_usage_rates` | Fig. 2 | `RQ1_정답지2024` |
| `fig2_constructs` | Fig. 3 | `구성개념` |
| `fig5_age_stereotype_slope` | Fig. 4 | `진단_연령경사오차` |
| `fig4_shortform_age` | Fig. 5 | `진단_숏폼연령` |
| `fig3_temporal_drift` | Fig. 6 | `RQ1_정답지2024`, `RQ1_2025문항셋` (2025 survey rates), `실측_연도변화` |
| `fig6_rq3_calibration` | Fig. 7 | `RQ3_보정`, `심사_보정형태민감도`, `RQ3_시점홀드아웃`, `심사_보정형태_시점홀드아웃` |
| `fig7_decision_flow` | Fig. 8 | TikZ source `code/fig7_decision_flow.tex` (no data) |

### Sheets without a producing script

The following sheets were transcribed from console output or from archived CSV/JSON files
rather than written by a script in `code/`; where the quantities could be recomputed from
archived files, this was done on 2026-09-04 and the result is stated.

- `진단_응답스타일`: partly transcribed from an unarchived console computation. `5점_평균` and
  the `1점%` to `5점%` columns are the unweighted distribution of the 24 raw 5-point item
  answers (reproduced in `심사_보조수치`: Gemini 2.45 with 19/33/33/15/0.4%, EXAONE 3.05 with
  5/27/30/34/5%). These raw-item means are **not** the values quoted in Sec. IV-C of the
  paper: the paper compares the eight post-stratified construct estimates (Gemini 2.54,
  EXAONE 3.03) with the weighted survey mean of the same eight constructs (2.83), all of
  which come from the `구성개념` sheet and are recomputed in `심사_보조수치`.
  The `이진_예선택률` column originally carried transcribed values (0.549/0.602) whose
  definition was not recorded and which none of the candidate definitions reproduces. In
  v1.12 the column was restated on the basis the paper uses, the mean post-stratified rate
  over the eight binary indicators (Gemini 0.516, EXAONE 0.575, survey 0.559; identical to
  the mean of the model columns of `RQ1_전체일치도`), with the unweighted pooled rate kept
  in a separate column (0.533/0.582); `code/rr_misc_numbers.py` reproduces both, and the
  sheet's `비고` column records the change.
- `복수응답_K3`: per-pass RQ1 MAE and cell MAE of the three EXAONE passes
  (`outputs/synthetic_recoded_exaone.csv`, `_k2.csv`, `_k3.csv`), computed with the
  `compare_validity.py`/`rq1_metrics.py` formulas against the full 2024 sample (recomputed:
  15.0/15.4/15.1 and 15.9/16.0/16.0, identical to the sheet).
- `M1_분산_Gemini`, `M1_분산_EXAONE`: `outputs/m1_variance_gemini.csv` and
  `outputs/m1_variance_exaone.csv` (written by `m1_variance.py`, live API calls) with the
  `모델` column prepended.
- `M2_ablation`: `outputs/m2_ablation.csv`, itself a console transcription; the three
  quantities are the RQ1 post-stratified MAE, the age-axis MAE, and the sex-by-age cell MAE
  (`compare_validity.py`, `sensitivity_sample.py`, `rq2_expand.py` formulas, full 2024
  sample) of `outputs/synthetic_recoded_{gemini,exaone}.csv` and
  `outputs/synthetic_recoded_demo_{gemini,exaone}.csv` (recomputed: identical to the sheet).
- `진단_프레이밍통제`: `outputs/framing_exp_{gemini,exaone}.json` (written by
  `framing_experiment.py`); `실측2024_숏폼%` (69.6) is the weighted 2024 survey rate of
  `RQ1_정답지2024`.
- `RQ2_십대제외강건성`: derived values; `DPD_e_전체14셀` (52.4/36.2) is the `rq2_expand.py`
  console output (mean of the rounded per-indicator ranges, see "Sample conventions"),
  `DPD_e_십대제외12셀` is `십대제외_RQ2`, the OTT age slopes are the full-data linear fit of
  the cell error on the age band (14 cells: `심사_보정계수`, `β1_전체자료`; 12 cells: the same
  fit without the teen cells), and `AI오차_10대`/`AI오차_70대+` are the pooled age-band errors of
  `심사_연령대별_부호오차`.
- `RQ1_2025문항셋`: no archived script writes it; the `build_dual_tables.py` formulas applied
  to `outputs/synthetic_recoded_2025_{gemini,exaone}.csv` against the full 2025 sample
  reproduce every value (verified).
- `설계기반_분산`, `민감도_표본cap`: now written by `design_variance.py` and
  `sensitivity_sample.py` (sheet-writing blocks added 2026-09-04); re-running both reproduces
  the archived sheets value for value.
- `요약`: headline values transcribed as literals in `build_paper_tables.py`.

### Bootstrap conventions

Model comparisons (`code/rr_paired_bootstrap.py`) are fully paired: each of the B = 600
replicates draws one household resample of the survey and one resample of the personas that
both panels answered validly, and applies both to the two panels. Point estimates use the
same paired personas (8,165 for the 2024 comparison, 8,168 and 8,092 for the temperature
contrasts, 7,794 for 2025), which the sheet records in the `짝 페르소나 n` column.
Every column of Table 8, including both empirical Bayes estimators, is computed inside the
same 200 stratified splits by `code/rr_calibration_forms_extended.py` (columns `syn_eb%p`
and `real_eb%p` of `심사_보정형태_학습곡선`, with the paired differences
`Δ(중첩−실측EB)` and `Δ(합성EB−실측EB)`), so the paper's comparisons between the
calibrated panel and the shrinkage estimator are paired. Three sheets run their own 200 splits under the same protocol and therefore differ from
Table 8 by up to 0.1 pp on the columns they share: `심사_EB풀링곡선` (kept for continuity
since v1.6; the paper no longer quotes it), `RQ3_실측단독_학습곡선`, and
`심사_학습곡선_정밀`. The difference arises because `rr_calibration_forms_extended.py`
consumes its random stream inside the nested selection, so its split sequence diverges from
the other scripts' after the first replicate. The paper quotes
`심사_보정형태_학습곡선` throughout.

Approximate runtimes on a 2026 laptop: `rr_calibration_forms_extended.py` about 100 s,
`rr_paired_bootstrap.py` about 25 s, `rr_order_analysis.py` about 7 s,
`rr_eb_curve.py` about 8 s, `rr_calibration_details.py` about 5 s; `quickstart.py` about 3 s.

The shrinkage weight of the empirical Bayes estimators uses each cell's sampling variance
p(1-p)/n_eff, where n_eff is the Kish effective sample size computed **on the respondents who
answered that item** (`rr_common.Real.cell_neff(mask, v)`). Two items, YouTube and short-form
use, were fielded to a module of 7,346 of the 8,675 respondents aged 10 and over, so their
effective sample sizes are smaller than the panel-wide ones; before v1.15 the panel-wide value
was used for every item, which understated the sampling variance of those two items by up to a
factor of 2.5 in the worst cell. The correction moved the empirical Bayes means by at most
0.05 pp; it moved the effective-sample-size-weighted linear fit (`심사_보정형태민감도`,
`age_lin_w`) by 0.22 pp for Gemini and 0.06 pp for EXAONE, from 9.20/7.05 to 8.98/6.99.

Two-sided bootstrap p-values follow the add-one convention
(`rr_common.boot_p`): p = min{1, 2 min(k- + 1, k+ + 1)/(B + 1)}, so the smallest attainable
value is 2/(B + 1) rather than 1/B. The same rule applies to the persona-level bootstrap of the order
experiment (`code/rr_order_analysis.py`, B = 2,000).

### Sample conventions

Two survey samples are used. The RQ1 headline metrics (Table 4: MAE 17.1/15.0, Pearson
0.795/0.903, construct r 0.788/0.500; `rq1_metrics.py`, `build_dual_tables.py`,
`sensitivity_sample.py`, `design_variance.py`) post-stratify to the full 2024 sample (8,693
respondents, including 18 under 10). The cell-based analyses (RQ2, RQ3, paired comparisons)
and every `rr_*.py` script (`rr_common.load_real`) use the 8,675 respondents aged 10 and
over, because no persona is under 19 and the `10세미만` cells have no synthetic counterpart.
This accounts for the following small differences between sheets: `심사_상관_Spearman`
Pearson 0.904 (age 10 and over) vs. 0.903 in Table 4 (full sample); `심사_상관_구성개념`
0.787/0.502 (age 10 and over) vs. 0.788/0.500 (full sample). Two further differences are
rounding, not sample: `정답지차수_효과` EXAONE 2024 MAE 14.9 is the mean of the eight
per-indicator errors after each was rounded to one decimal (14.94), whereas Table 4's 15.0
averages the unrounded errors (14.95); `RQ2_십대제외강건성` R_e 52.4 is the mean of the eight
per-indicator ranges after each was rounded to one decimal (52.35), whereas 52.3 (paper,
`심사_집단오차지표`, `십대제외_RQ2`) averages the unrounded ranges (52.34).

### Development artifacts

`outputs/batch_check.csv`, `outputs/paid_check.csv`, `outputs/paid_check_3.csv`,
`outputs/parallel_check.csv`, and `outputs/trial_synthetic_20.csv` are pre-run connectivity
and billing checks of 2 July 2026 (small trial generations); no script in `code/` reads them
and no reported number depends on them.

## Quick start

`python quickstart.py` verifies the manifest, prints the headline table values from
the archived workbook, and regenerates Figs. 1–7 with matplotlib (Fig. 8 is a TikZ
source, `code/fig7_decision_flow.tex`, compiled when `pdflatex` is available; exit
code 1 if the manifest or the rendering fails); no KISDI access is required for these steps. The scripts that need the restricted microdata are listed at the end
of its output. `python3 rebuild_manifest.py --check` verifies `MANIFEST.sha256` on its own
without rewriting it.

## Environment

Python ≥ 3.10 with `pandas`, `numpy`, `scipy`, `openpyxl`, `matplotlib`; the exact versions used are pinned in `requirements.txt`. Generation
additionally requires `google-genai` (Gemini Batch API) and an OpenAI-compatible
client for the FriendliAI EXAONE endpoint. Hosted-model outputs reflect the
July 2026 serving snapshot recorded in `PROTOCOL.md`; regeneration may differ
if the hosted models drift (the EXAONE arm is open-weight and pinnable).

## Notes for verification

- Final exclusion rates by sex-by-age cell for the four main panels are in
  `outputs/failure_rates_by_cell.csv` (`목표_n`, `유효_n`, `형식실패율_%` = share of
  the cell excluded after all retries; every Gemini row is 0.00, EXAONE 2024 at most
  0.33% and EXAONE 2025 at most 7.5%; overall exclusions Gemini 0%, EXAONE ≤1.8%).
  First-attempt failure rates per cell exist only for the runs whose payloads were
  archived (the Gemini 2025 run and the demographic-only 2024 ablation) and are in
  sheet `심사_형식실패_셀별`; the Gemini 2024 main run's 66 first-attempt failures are
  known only per sub-batch (`PROTOCOL.md` §4a).
- The `logs/` payloads allow byte-level verification of the prompt protocol
  against `PROTOCOL.md` and `code/generate.py`.
