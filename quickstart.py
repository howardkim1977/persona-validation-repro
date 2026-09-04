# -*- coding: utf-8 -*-
"""Quick start for the reproducibility package (no KISDI access required).

Runs in three steps from the archived aggregate outputs:
  1. verifies the SHA-256 manifest of the package;
  2. prints the headline tables of the paper from outputs/validity_results.xlsx
     (RQ1 agreement, RQ2 segment error, RQ3 calibration vs. real-only estimators,
     format-failure rates, paired model comparison; table numbers follow the
     September 2026 manuscript);
  3. regenerates the matplotlib figures (Figs. 1-7) into paper/figures/; the decision
     flowchart (Fig. 8) is a TikZ source (code/fig7_decision_flow.tex) compiled with pdflatex if available.
Analyses that need the KISDI microdata (analysis_ready.csv) are listed at the end
with the script that reproduces each one once access has been granted.

Usage:  python quickstart.py            (from the package root)
        python quickstart.py --no-figures
"""
import argparse, hashlib, os, sys, subprocess
import pandas as pd

ROOT=os.path.dirname(os.path.abspath(__file__))
XLSX=os.path.join(ROOT,"outputs","validity_results.xlsx")
SHEETS=[("RQ1_지표종합","RQ1 overall agreement (Table 4)"),
        ("RQ2_축별MAE","RQ2 segment MAE, four of the five axes (Table 5)"),
        ("RQ2_지역축","RQ2 segment MAE, region axis (Table 5)"),
        ("심사_집단오차지표","RQ2 between-group error range and absolute-error complements"),
        ("심사_짝부트스트랩","Paired design-based bootstrap: Gemini vs. EXAONE (Sec. IV-A)"),
        ("RQ3_보정","RQ3 calibration, linear form (Table 7)"),
        ("심사_보정형태민감도","RQ3 calibration by correction form incl. nested selection (Table 7)"),
        ("심사_보정형태_학습곡선","RQ3 learning curve vs. real-only estimators (Table 8)"),
        ("심사_EB풀링곡선","Partially pooled estimators, earlier independent split run (superseded by 심사_보정형태_학습곡선; not quoted in the paper)"),
        ("RQ3_시점홀드아웃","Temporal holdout (Table 7, middle)"),
        ("심사_형식실패","Format-failure and exclusion rates (Table 2)")]

def verify_manifest():
    man=os.path.join(ROOT,"MANIFEST.sha256"); bad=0; n=0
    for line in open(man,encoding="utf-8"):
        h,name=line.strip().split("  ",1); p=os.path.join(ROOT,name)
        if not os.path.exists(p): print("  missing:",name); bad+=1; continue
        d=hashlib.sha256(open(p,"rb").read()).hexdigest(); n+=1
        if d!=h: print("  hash mismatch:",name); bad+=1
    print(f"[1/3] manifest: {n} files checked, {bad} problems"); return bad

def print_tables():
    x=pd.ExcelFile(XLSX); pd.set_option("display.width",160); pd.set_option("display.max_columns",30)
    for sheet,title in SHEETS:
        if sheet not in x.sheet_names: print(f"  (sheet {sheet} not found)"); continue
        print(f"\n--- {title} [{sheet}] ---"); print(x.parse(sheet).to_string(index=False))
    print("\n[2/3] headline tables printed")

def render_figures():
    r=subprocess.run([sys.executable,os.path.join(ROOT,"code","render_figures.py")],cwd=ROOT)
    print("[3/3] figures 1-7:", "ok" if r.returncode==0 else f"failed ({r.returncode})")
    import shutil
    if shutil.which("pdflatex"):
        fig=os.path.join(ROOT,"paper","figures"); os.makedirs(fig,exist_ok=True)
        shutil.copy(os.path.join(ROOT,"code","fig7_decision_flow.tex"),fig)
        t=subprocess.run(["pdflatex","-interaction=nonstopmode","fig7_decision_flow.tex"],cwd=fig,capture_output=True)
        print("      figure 8 (TikZ):", "ok" if t.returncode==0 else f"failed ({t.returncode})")
    else: print("      figure 8 (TikZ): pdflatex not found; compile code/fig7_decision_flow.tex manually")
    return r.returncode

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--no-figures",action="store_true"); a=ap.parse_args()
    bad=verify_manifest(); print_tables()
    rc=0 if a.no_figures else render_figures()
    if bad or rc: sys.exit(1)
    print("\nAnalyses requiring KISDI microdata (analysis_ready.csv; 10 of them, see README for the full list):\n"
          "  rq1_metrics.py, rq2_expand.py, rq3_realonly.py, rr_paired_bootstrap.py, rr_calibration_forms_extended.py,\n"
          "  rr_eb_curve.py, rr_teen19.py, rr_construct_corr.py, rr_hier_bootstrap.py, rr_order_analysis.py")
