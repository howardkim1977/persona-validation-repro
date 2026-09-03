# Reproducibility Package

**Paper:** Distributional Validity of a Korean Synthetic Persona Panel: Evidence
from the Korea Media Panel Survey (IEEE Access, under review; earlier working
title: "Distributional Validity and Calibration of a Korean Synthetic Persona
Panel for Digital and AI Service Use: A Secondary-Data Validation Against the
Korea Media Panel Survey")

**Preprint:** arXiv:2608.28615, https://doi.org/10.48550/arXiv.2608.28615;
SocArXiv, https://doi.org/10.31235/osf.io/zb3w2_v1

**Archived package:** Zenodo — v1.10 (September 2026) https://doi.org/10.5281/zenodo.22284555;
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
| `outputs/` | Raw synthetic responses of all full-panel runs, recoded response files, aggregate results workbook (`validity_results.xlsx`), per-cell format-failure rates, and the wording experiment's arm-level results (`framing_exp_*.json`; per-persona pairing was not retained, see `PROTOCOL.md`) |
| `logs/` | Gemini Batch API request payloads exactly as sent (`batch_w2025_*.jsonl`: 2025 run; `batch_w2024_*.jsonl`: demographic-only 2024 ablation run, see `PROTOCOL.md` §4a; `order_*.jsonl` and `order_exp_gemini_R1_orders.json`: randomized-order experiment) and the console logs of every generation run (`run_*.log`, `recover_*.log`, `framing_*.log`, `order_exp_gemini.log`) |
| `PROTOCOL.md` | Prompt protocol: persona block construction, system/user templates (verbatim), JSON output contract, skip logic, retry rules, model identifiers/endpoints/serving window |
| `DATASET_HASHES.txt` | SHA-256 of the exact Nemotron-Personas-Korea file used, plus the sampling seed |
| `MANIFEST.sha256` | SHA-256 of every file in this package |

## What is *not* included, and why

- **KISDI Korea Media Panel Survey microdata** (`analysis_ready.csv`,
  `PanelData_*.csv`): access-restricted. Apply at the KISDI Media Statistics
  Portal (https://stat.kisdi.re.kr); after approval, `code/recode.py` documents
  the exact recoding from the raw KISDI file to the analysis schema used here.
  All analyses that require real data read `analysis_ready.csv` (column schema
  visible at the top of each analysis script). Scripts that resample by
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

## Reproduction map (paper table/figure → script → workbook sheet)

Numbering follows the September 2026 version of the manuscript.

| Paper item | Script | Workbook sheet |
|---|---|---|
| Table 1 (model identifiers) | `PROTOCOL.md` §5 | — |
| Table 2 (format failures) | `rr_failure_cost.py` | `심사_형식실패`, `심사_형식실패_셀별`, `심사_생성규모` |
| Table 3 (analysis status) | `PREREGISTRATION_MAP.md` | — |
| Table 4 (RQ1 metrics), paired model comparison, Spearman | `rq1_metrics.py`, `rr_paired_bootstrap.py` | `RQ1_지표종합`, `심사_짝부트스트랩`, `심사_상관_Spearman`, `심사_상관_구성개념` |
| Table 5 (RQ2 axes, signed-error range and complements) | `rq2_expand.py`, `rq2_region.py`, `rr_dpd_supplements.py` | `RQ2_축별MAE`, `RQ2_지역축`, `심사_집단오차지표`, `심사_집단오차_지표별` |
| 19-year-old comparison (Sec. IV-B) | `rr_teen19.py` | `심사_10대_19세비교` |
| Table 6 (framing experiment) | `framing_experiment.py`, `rr_framing_tests.py`, `diagnose_bias.py` | `진단_프레이밍통제`, `심사_프레이밍검정` |
| Table 7 (calibration by form; temporal holdout) | `rq_uncertainty.py`, `rr_calibration_details.py`, `rr_calibration_forms_extended.py` | `RQ3_보정`, `심사_보정형태민감도`, `심사_보정형태_시점홀드아웃` |
| Table 8 (learning curve vs. real-only; EB shrinkage; entire-cell holdout) | `rr_calibration_forms_extended.py`, `rr_learning_curve.py`, `rr_eb_curve.py` | `심사_보정형태_학습곡선`, `심사_학습곡선_정밀`, `심사_EB풀링곡선`, `심사_보정형태_셀홀드아웃` |
| Table 9 (baselines, ablation) | `rq3_temporal_baseline.py`, `rr_baselines_common6.py`, `sensitivity_teen_excluded.py`, `m2_ablation` run of `generate.py` | `베이스라인_공통6`, `베이스라인_공통6_보정`, `RQ3_시점홀드아웃`, `십대제외_베이스라인`, `M2_ablation` |
| Table 11 (teen-excluded sensitivity) | `sensitivity_teen_excluded.py`, `rr_teen_nested.py` | `십대제외_*`, `심사_십대제외_보정형태` |
| Tables 12–13 (signed error by age band) | derived from the sex-by-age cell errors of `rq2_expand.py` (the two sex cells of each band combined) | `RQ2_셀별상세` |
| Table 14 (calibration coefficients, residuals) | `rr_calibration_details.py` | `심사_보정계수` |
| Table 15 (construct correlation structure) | `rr_construct_corr.py` | `심사_구성개념_상관요약`, `심사_구성개념_상관행렬` |
| Hierarchical bootstrap (Sec. IV-J) | `rr_hier_bootstrap.py`, `rr_order_analysis.py` | `심사_계층부트스트랩_EXAONE`, `심사_계층부트스트랩_Gemini` |
| Table 10 (randomized-order experiment, Sec. IV-K) | `order_experiment.py`, `rr_order_analysis.py` | `심사_순서실험_*` |
| Design-based CIs (Kish deff, household bootstrap) | `design_variance.py` | `설계기반_분산` |
| Sampling-cap sensitivity (Sec. III-G) | `sensitivity_sample.py` | `민감도_표본cap` |
| Item-bootstrap correlation CIs (Sec. IV-A) | `rr_item_bootstrap.py` | `심사_문항부트스트랩` |
| Median absolute error and leave-one-item-out MAE (Secs. IV-A, IV-E) | `rr_item_supplements.py` | `심사_문항보조통계` |
| Response stability (ICC, repeated passes) | `m1_variance.py`, `recover_k2.py`, `recover_k23.py` | `M1_분산_Gemini`, `M1_분산_EXAONE`, `복수응답_K3` |
| Figures (all) | `render_figures.py`; decision flowchart (Fig. 8) `fig7_decision_flow.tex` (TikZ) | (values transcribed from the sheets above as literals in the script) |

## Quick start

`python quickstart.py` verifies the manifest, prints the headline table values from
the archived workbook, and regenerates Figs. 1–7 with matplotlib (Fig. 8 is a TikZ
source, `code/fig7_decision_flow.tex`, compiled when `pdflatex` is available; exit
code 1 if the manifest or the rendering fails); no KISDI access is required for these steps. The scripts that need the restricted microdata are listed at the end
of its output.

## Environment

Python ≥ 3.10 with `pandas`, `numpy`, `scipy`, `openpyxl`, `matplotlib`; the exact versions used are pinned in `requirements.txt`. Generation
additionally requires `google-genai` (Gemini Batch API) and an OpenAI-compatible
client for the FriendliAI EXAONE endpoint. Hosted-model outputs reflect the
July 2026 serving snapshot recorded in `PROTOCOL.md`; regeneration may differ
if the hosted models drift (the EXAONE arm is open-weight and pinnable).

## Notes for verification

- Format-failure rates by sex-by-age cell are in
  `outputs/failure_rates_by_cell.csv` (overall exclusions: Gemini 0%, EXAONE ≤1.8%);
  the Gemini 2024 first-attempt rows there come from the demographic-only
  ablation run (`PROTOCOL.md` §4a).
- The `logs/` payloads allow byte-level verification of the prompt protocol
  against `PROTOCOL.md` and `code/generate.py`.
