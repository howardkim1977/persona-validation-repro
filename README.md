# Reproducibility Package

**Paper:** Distributional Validity and Calibration of a Korean Synthetic Persona
Panel for Digital and AI Service Use: A Secondary-Data Validation Against the
Korea Media Panel Survey (submitted to IEEE Access)

**Preprint:** SocArXiv, https://doi.org/10.31235/osf.io/zb3w2_v1

**Archived package:** Zenodo, https://doi.org/10.5281/zenodo.21397425

**Preregistration:** OSF registration `dfe2z` (https://osf.io/dfe2z) — see
`PREREGISTRATION_MAP.md` for the item-by-item correspondence between the
registration and the reported analyses.

## Contents

| Path | Contents |
|---|---|
| `code/` | All generation, recoding, analysis, calibration, and figure scripts (Python) |
| `outputs/` | Raw synthetic responses (all conditions), recoded response files, aggregate results workbook (`validity_results.xlsx`), per-cell format-failure rates |
| `logs/` | Raw Gemini Batch API request payloads (`batch_*.jsonl`) — system instruction, full item text, and sampling parameters (temperature, top_p, thinking level) exactly as sent |
| `PROTOCOL.md` | Prompt protocol: persona block construction, system/user templates (verbatim), JSON output contract, skip logic, retry rules, model identifiers/endpoints/serving window |
| `DATASET_HASHES.txt` | SHA-256 of the exact Nemotron-Personas-Korea file used, plus the sampling seed |
| `MANIFEST.sha256` | SHA-256 of every file in this package |

## What is *not* included, and why

- **KISDI Korea Media Panel Survey microdata** (`analysis_ready.csv`,
  `PanelData_*.csv`): access-restricted. Apply at the KISDI Media Statistics
  Portal (https://stat.kisdi.re.kr); after approval, `code/recode.py` documents
  the exact recoding from the raw KISDI file to the analysis schema used here.
  All analyses that require real data read a single file `analysis_ready.csv`
  with the column schema visible at the top of each analysis script.
- **API keys**: all scripts read credentials from environment variables
  (`GEMINI_API_KEY`, `EXAONE_*`); none are stored in code.
- **Nemotron-Personas-Korea** (~4.1 GB): publicly available on Hugging Face
  (`nvidia/Nemotron-Personas-Korea`); verify the exact file with
  `DATASET_HASHES.txt`.

## Reproduction map (paper table/figure → script → workbook sheet)

| Paper item | Script | Workbook sheet |
|---|---|---|
| Table 1 (RQ1 metrics) | `rq1_metrics.py` | `RQ1_지표종합` |
| Table 2 (RQ2 axes, DPD_e) | `rq2_expand.py`, `rq2_region.py` | `RQ2_축별MAE`, `RQ2_지역축`, `RQ2_집단편향_*` |
| Table 3 (framing experiment) | `framing_experiment.py`, `diagnose_bias.py` | `진단_프레이밍통제` |
| Table 4 (calibration + temporal holdout) | `rq_uncertainty.py`, `rq3_temporal_baseline.py` | `RQ3_보정`, `RQ3_시점홀드아웃` |
| Table 5 (real-only learning curve, cell holdout) | `rq3_realonly.py` | `RQ3_실측단독_학습곡선`, `RQ3_셀홀드아웃` |
| Table 6 (baselines, ablation) | `rq3_temporal_baseline.py`, `sensitivity_teen_excluded.py` | `십대제외_베이스라인` (full-sample rows), `M2_ablation` |
| Appendix teen-excluded sensitivity | `sensitivity_teen_excluded.py` | `십대제외_*` (6 sheets) |
| Appendix signed error by age band | `diagnose_bias.py` | `진단_연령경사` |
| Design-based CIs (Kish deff, household bootstrap) | `design_variance.py` | `설계기반_분산` |
| Response stability (ICC, repeated passes) | `m1_variance.py`, `recover_k2.py`, `recover_k23.py` | `M1_*` |
| Figures 1–7 | `render_figures.py` | (reads the sheets above) |

## Environment

Python ≥ 3.10 with `pandas`, `numpy`, `openpyxl`, `matplotlib`. Generation
additionally requires `google-genai` (Gemini Batch API) and an OpenAI-compatible
client for the FriendliAI EXAONE endpoint. Hosted-model outputs reflect the
July 2026 serving snapshot recorded in `PROTOCOL.md`; regeneration may differ
if the hosted models drift (the EXAONE arm is open-weight and pinnable).

## Notes for reviewers

- Format-failure rates by sex-by-age cell are in
  `outputs/failure_rates_by_cell.csv` (overall: Gemini 0%, EXAONE ≤1.8%).
- The `logs/` payloads allow byte-level verification of the prompt protocol
  against `PROTOCOL.md` and `code/generate.py`.
