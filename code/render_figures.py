# -*- coding: utf-8 -*-
"""논문용 벡터 그림 렌더링(영문 라벨, 흑백 대비 마커/해치).
출력: paper/figures/*.pdf(벡터) + *.png(미리보기). 수치 출처: outputs/validity_results.xlsx(값을 리터럴로 옮겨 적음).
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT="paper/figures"; os.makedirs(OUT,exist_ok=True)
plt.rcParams.update({"font.size":9,"axes.linewidth":0.6,"axes.edgecolor":"#888781",
    "xtick.color":"#52514e","ytick.color":"#52514e","axes.labelcolor":"#333",
    "figure.dpi":150,"savefig.bbox":"tight","pdf.fonttype":42,"font.family":"DejaVu Sans"})
GRAY,BLUE,TEAL,DARK,RED,AMBER="#8a8880","#2a78d6","#1baf7a","#5f5e5a","#e34948","#eda100"

def save(fig,name):
    fig.savefig(f"{OUT}/{name}.pdf"); fig.savefig(f"{OUT}/{name}.png",dpi=300); plt.close(fig)
    print("저장:",name)

BINS=["AI use","OTT","YouTube","Short-form","SNS","Messenger","Metaverse","Subscription"]

# Fig 1 — RQ1 이용률(실측2024 vs 합성)
def fig1():
    act=[13.7,89.2,93.2,69.6,60.7,92.2,5.6,22.7]; gem=[39.9,64.5,97.0,25.2,48.0,97.6,2.0,38.8]; exa=[37.1,83.7,86.6,51.4,74.4,69.4,13.6,44.1]
    y=range(len(BINS)); h=0.26
    fig,ax=plt.subplots(figsize=(6.6,3.6))
    ax.barh([i+h for i in y],act,h,color=GRAY,label="Survey 2024 (weighted)",edgecolor="white",linewidth=0.4)
    ax.barh(list(y),gem,h,color=BLUE,label="Gemini",hatch="//",edgecolor="white",linewidth=0.4)
    ax.barh([i-h for i in y],exa,h,color=TEAL,label="EXAONE",hatch="..",edgecolor="white",linewidth=0.4)
    ax.set_yticks(list(y)); ax.set_yticklabels(BINS); ax.invert_yaxis()
    ax.set_xlabel("Usage rate (%)"); ax.set_xlim(0,100)
    ax.legend(frameon=False,fontsize=8,loc="lower right"); ax.grid(axis="x",color="#e1e0d9",lw=0.5)
    for s in ["top","right"]: ax.spines[s].set_visible(False)
    save(fig,"fig1_rq1_usage_rates")

# Fig 2 — 구성개념 평균
def fig2():
    C=["Innov.\n(Functional)","Innov.\n(Hedonic)","Innov.\n(Social)","Innov.\n(Cognitive)","Accept.\n(Perf.)","Accept.\n(Effort)","Accept.\n(Social)","Accept.\n(Facil.)"]
    act=[2.58,2.88,2.72,2.54,3.16,3.06,2.85,2.84]; gem=[2.25,3.02,1.66,1.86,3.26,2.71,2.60,2.92]; exa=[3.02,3.35,2.77,3.02,3.66,3.47,2.26,2.73]
    x=range(len(C)); w=0.26
    fig,ax=plt.subplots(figsize=(6.6,3.2))
    ax.bar([i-w for i in x],act,w,color=GRAY,label="Survey (weighted)",edgecolor="white",linewidth=0.4)
    ax.bar(list(x),gem,w,color=BLUE,label="Gemini",hatch="//",edgecolor="white",linewidth=0.4)
    ax.bar([i+w for i in x],exa,w,color=TEAL,label="EXAONE",hatch="..",edgecolor="white",linewidth=0.4)
    ax.set_xticks(list(x)); ax.set_xticklabels(C,fontsize=7.5); ax.set_ylabel("Mean (5-point)"); ax.set_ylim(1,4)
    ax.legend(frameon=False,fontsize=8,ncol=3,loc="upper center"); ax.grid(axis="y",color="#e1e0d9",lw=0.5)
    for s in ["top","right"]: ax.spines[s].set_visible(False)
    save(fig,"fig2_constructs")

# Fig 3 — 시점 드리프트
def fig3():
    a24=[13.7,89.2,93.2,69.6,60.7,92.2,5.6,22.7]; a25=[31.6,90.9,95.5,86.5,64.2,93.8,7.3,22.3]
    gem=[39.9,64.5,97.0,25.2,48.0,97.6,2.0,38.8]; exa=[37.1,83.7,86.6,51.4,74.4,69.4,13.6,44.1]
    y=range(len(BINS)); h=0.2
    fig,ax=plt.subplots(figsize=(6.6,3.8))
    ax.barh([i+1.5*h for i in y],a24,h,color="#c3c2b7",label="Survey 2024",edgecolor="white",linewidth=0.3)
    ax.barh([i+0.5*h for i in y],a25,h,color=DARK,label="Survey 2025",edgecolor="white",linewidth=0.3)
    ax.barh([i-0.5*h for i in y],gem,h,color=BLUE,label="Gemini",hatch="//",edgecolor="white",linewidth=0.3)
    ax.barh([i-1.5*h for i in y],exa,h,color=TEAL,label="EXAONE",hatch="..",edgecolor="white",linewidth=0.3)
    ax.set_yticks(list(y)); ax.set_yticklabels(BINS); ax.invert_yaxis()
    ax.set_xlabel("Usage rate (%)"); ax.set_xlim(0,100)
    ax.legend(frameon=False,fontsize=8,loc="lower right"); ax.grid(axis="x",color="#e1e0d9",lw=0.5)
    for s in ["top","right"]: ax.spines[s].set_visible(False)
    save(fig,"fig3_temporal_drift")

# Fig 4 — 연령대별 숏폼
def fig4():
    ages=["10s","20s","30s","40s","50s","60s","70s+"]
    act=[88.7,94.7,94.1,88.9,83.1,78.3,76.6]; gem=[75.9,43.2,10.9,2.5,1.2,0.5,0.2]; exa=[42.7,39.1,34.4,30.1,25.4,21.1,17.2]
    fig,ax=plt.subplots(figsize=(5.0,3.2))
    ax.plot(ages,act,color=DARK,marker="s",lw=1.8,label="Survey 2025")
    ax.plot(ages,gem,color=BLUE,marker="o",lw=1.6,ls="--",label="Gemini")
    ax.plot(ages,exa,color=TEAL,marker="^",lw=1.6,ls=":",label="EXAONE")
    ax.set_ylabel("Short-form usage (%)"); ax.set_xlabel("Age group"); ax.set_ylim(0,100)
    ax.legend(frameon=False,fontsize=8); ax.grid(color="#e1e0d9",lw=0.5)
    for s in ["top","right"]: ax.spines[s].set_visible(False)
    save(fig,"fig4_shortform_age")

# Fig 5 — 연령경사 오차
def fig5():
    labs=["OTT","Short-form","SNS","Subscription","AI use","YouTube","Messenger","Metaverse"]
    gem=[-12.4,-8.6,-7.9,-7.1,-5.4,-4.3,-0.1,2.8]; exa=[1.5,-1.5,2.5,2.6,0.6,-5.7,-3.6,2.7]
    y=range(len(labs)); h=0.36
    fig,ax=plt.subplots(figsize=(5.4,3.4))
    ax.barh([i+h/2 for i in y],gem,h,color=BLUE,label="Gemini",hatch="//",edgecolor="white",linewidth=0.4)
    ax.barh([i-h/2 for i in y],exa,h,color=TEAL,label="EXAONE",hatch="..",edgecolor="white",linewidth=0.4)
    ax.axvline(0,color="#888781",lw=0.7)
    ax.set_yticks(list(y)); ax.set_yticklabels(labs); ax.invert_yaxis()
    ax.set_xlabel("Age slope of error (pp per age step)\n(negative = under-estimated for older)")
    ax.legend(frameon=False,fontsize=8,loc="lower left"); ax.grid(axis="x",color="#e1e0d9",lw=0.5)
    for s in ["top","right"]: ax.spines[s].set_visible(False)
    save(fig,"fig5_age_stereotype_slope")

# Fig 6 — RQ3 보정
def fig6():
    # 동시점(within-2024) vs 시점밖(2024→2025): 무보정 / 선형 연령회귀(사전지정) / 중첩 선택(nested).
    # 값은 본문 Table 7 및 심사_보정형태_* 시트와 동일.
    models=["Gemini","EXAONE"]
    ind=[[18.9,15.9],[8.6,6.7],[5.2,4.5]]; oot=[[21.0,18.3],[14.5,14.0],[12.4,12.7]]
    GM=12.1; PW=6.7
    import numpy as _np
    x=_np.arange(len(models)); w=0.13
    fig,ax=plt.subplots(figsize=(5.6,3.3))
    labs=["Uncorrected","Linear age (post-hoc)","Nested selection"]; cols=[RED,BLUE,TEAL]
    for i,(vals,lab,c) in enumerate(zip(ind,labs,cols)):
        ax.bar(x+(i-2.5)*w,vals,w,color=c,label=f"{lab}, within-2024",edgecolor="white",linewidth=0.4)
    for i,(vals,lab,c) in enumerate(zip(oot,labs,cols)):
        ax.bar(x+(i+0.5)*w,vals,w,color=c,hatch="//",label=f"{lab}, out-of-time",edgecolor="white",linewidth=0.4)
    ax.axhline(GM,color="#6b6a66",lw=1.0,ls="--"); ax.text(1.97,GM+0.25,f"grand-mean {GM}",fontsize=7.2,color="#3a3a38",ha="right")
    ax.axhline(PW,color="#6b6a66",lw=1.0,ls=":");  ax.text(1.97,PW+0.25,f"prior-wave {PW}",fontsize=7.2,color="#3a3a38",ha="right")
    ax.set_xticks(x); ax.set_xticklabels(models); ax.set_ylabel("Held-out segment MAE (pp)"); ax.set_xlim(-0.55,2.02); ax.set_ylim(0,25)
    ax.legend(frameon=False,fontsize=6.6,ncol=2,loc="upper center"); ax.grid(axis="y",color="#e1e0d9",lw=0.5)
    for s_ in ["top","right"]: ax.spines[s_].set_visible(False)
    save(fig,"fig6_rq3_calibration")


# Fig 0 — 연구 틀(프레임워크) 개요. 본문 Fig.1로 삽입(파일 번호는 유지).
def fig0():
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    GRAY,BLUE2,TEAL2,AMBER2="#f0efec","#e6f1fb","#e1f5ee","#faeeda"
    DARK,EB,ET,EG,EA="#52514e","#185fa5","#0f6e56","#888781","#854f0b"
    fig,ax=plt.subplots(figsize=(7.05,3.2)); ax.axis("off")
    ax.set_xlim(0,100); ax.set_ylim(-4,100)
    def box(x,y,w,h,title,lines,fc,ec,tc=DARK):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.6",fc=fc,ec=ec,lw=0.9))
        ax.text(x+w/2,y+h-4.2,title,ha="center",va="top",fontsize=7.6,fontweight="bold",color=tc)
        ax.text(x+w/2,y+h-10.8,"\n".join(lines),ha="center",va="top",fontsize=6.3,color="#3a3a38",linespacing=1.28)
    def seg(x1,y1,x2,y2,c=EG):
        ax.plot([x1,x2],[y1,y2],color=c,lw=1.1,solid_capstyle="round",zorder=1)
    def arr(x1,y1,x2,y2,c=EG):
        ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=9,
                                     color=c,lw=1.1,shrinkA=0,shrinkB=1,zorder=1))
    box(1,64,20,32,"Persona source",
        ["Nemotron-Personas-","Korea (~1M records,","26 fields; no real","individuals)"],GRAY,EG)
    box(26,64,20,32,"Stratified sampling",
        ["14 sex-by-age cells","n = clip(2n, 200, 600)","8,168 personas/model","(2024 item set)"],GRAY,EG)
    box(51,64,24,32,"LLM generation",
        ["Gemini 3.5 Flash | EXAONE","full questionnaire (Korean)","JSON; \u22643 regen; skip logic","temp 1.0 (0.7 robustness)"],BLUE2,EB,EB)
    box(80,64,19,32,"Synthetic panel",
        ["recode to survey","schema;","post-stratified","cell estimates"],BLUE2,EB,EB)
    arr(21,80,26,80); arr(46,80,51,80); arr(75,80,80,80)
    box(1,12,26,32,"Survey reference",
        ["KISDI Media Panel","2024 n=8,693 | 2025 n=8,411","2023 = prior-wave baseline","weighted (household clusters)"],GRAY,EG)
    box(33,10,31,36,"Validation & diagnostics",
        ["RQ1 agreement: MAE, KL, r","(design-based bootstrap)","RQ2 five-axis segment error, $R_e$","temporal mismatch, bias signatures,","framing, ablation, baselines, variance"],TEAL2,ET,ET)
    box(69,10,30,36,"RQ3 calibration",
        ["holdout \u00d7200 + real-only baselines","+ entire-cell & temporal holdouts","correction form selected inside","the calibration set (nested)","\u2192 niche: data-scarce settings only"],AMBER2,EA,EA)
    seg(89.5,64,89.5,55,c=EB); seg(89.5,55,48.5,55,c=EB); arr(48.5,55,48.5,46,c=EB)
    arr(27,28,33,28); arr(64,28,69,28,c=ET)
    seg(14,12,14,5); seg(14,5,84,5); arr(84,5,84,10)
    ax.text(49,0.6,"30% real calibration sample",fontsize=6.0,color="#6b6a66",ha="center",va="top")
    save(fig,"fig0_framework")

for f in [fig0,fig1,fig2,fig3,fig4,fig5,fig6]: f()
print("완료: paper/figures/ (7개 PDF+PNG)")
