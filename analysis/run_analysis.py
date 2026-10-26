#!/usr/bin/env python3
"""Reproduce aggregate meta-analyses and make publication-ready overview plots."""
import hashlib
import json
from pathlib import Path
import platform
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator,FuncFormatter,NullLocator
import numpy as np
import pandas as pd
import scipy
from scipy import stats
import statsmodels

from meta_analysis import analyze_counts,leave_one_out,pool_effects,sensitivity,trial_effects

BASE=Path(__file__).resolve().parent
ROOT=BASE.parent
DATA=BASE/"data"
OUT=BASE/"output"
TEAL="#087F8C"
ORANGE="#C87631"
INK="#20343F"
GRAY="#6D7B84"
PALETTE=["#A6C8D2","#6DAEBE","#3A94A9","#147387","#064F62"]

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"text.color":INK,"axes.labelcolor":INK,"axes.edgecolor":"#CBD4D8","axes.spines.top":False,"axes.spines.right":False,"axes.titlesize":14,"axes.labelsize":11,"xtick.color":GRAY,"ytick.color":INK,"xtick.labelsize":10,"ytick.labelsize":11,"savefig.facecolor":"white","figure.facecolor":"white","svg.fonttype":"none","pdf.fonttype":42})

def save_figure(fig,name):
    for suffix in ["png","pdf","svg"]:
        fig.savefig(OUT/(name+"."+suffix),dpi=230,bbox_inches="tight")
    plt.close(fig)

def forest_axis(ax,ticks,limits):
    ax.set_xscale("log")
    ax.set_xlim(*limits)
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v,p:f"{v:g}"))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.axvline(1,color="#89979E",ls=(0,(4,4)),lw=1,zorder=0)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y',length=0,pad=9)
    ax.grid(axis='x',color="#EBEFF1",lw=.8,zorder=0)

def interval(ax,rr,lo,hi,y,color=TEAL,marker='o',size=6,alpha=1):
    ax.plot([lo,hi],[y,y],color=color,lw=1.7,alpha=alpha,zorder=2)
    ax.plot(rr,y,marker=marker,color=color,ms=size,alpha=alpha,zorder=3)

def overview(summary):
    risk=pd.read_csv(DATA/"ctt_2012_risk_effects.csv")
    projection=pd.read_csv(DATA/"ctt_2012_absolute_projections.csv")
    pooled=pd.read_csv(DATA/"uspstf_2022_pooled_outcomes.csv")
    fig=plt.figure(figsize=(15.5,11.4))
    fig.text(.06,.968,"Statins before a first cardiovascular event",fontsize=24,weight='bold')
    fig.text(.06,.934,"Published evidence and a reproducible trial-level check",fontsize=13,color=GRAY)
    fig.text(.06,.879,"A  Benefit is present before established vascular disease",fontsize=14,weight='bold')
    fig.text(.06,.852,"Major vascular events by predicted five-year risk",fontsize=11,color=GRAY)
    ax=fig.add_axes([.105,.555,.335,.258])
    for population,color,offset,marker in [("No previous vascular disease",TEAL,.12,'o'),("Previous vascular disease",ORANGE,-.12,'s')]:
        d=risk.loc[risk.population==population].sort_values('risk_order')
        for _,r in d.iterrows():
            y=5-r.risk_order+offset
            interval(ax,r.rr_per_1_mmol_ldl,r.ci_low,r.ci_high,y,color,marker,7 if r.is_summary else 5.5)
    ax.axhline(.6,color="#D5DDE0",lw=.8)
    ax.set_yticks(range(6),["All risk groups","≥30%","20–<30%","10–<20%","5–<10%","<5%"])
    ax.set_ylim(-.55,5.65)
    forest_axis(ax,[.3,.5,.75,1,1.5],(.28,1.8))
    ax.set_xlabel("Rate ratio per 1 mmol/L LDL reduction")
    ax.legend([Line2D([],[],color=TEAL,marker='o',lw=1.5),Line2D([],[],color=ORANGE,marker='s',lw=1.5)],["No previous vascular disease","Previous vascular disease"],fontsize=9.5,loc='lower left',bbox_to_anchor=(-.02,1.01),frameon=False,ncol=1,borderaxespad=0,handlelength=1.4,labelspacing=.2)
    fig.text(.105,.491,"Strata: 99% intervals; summaries: 95%. CTT 2012, Figure 2.",fontsize=9.5,color=GRAY)

    fig.text(.57,.879,"B  Absolute benefit increases with baseline risk",fontsize=14,weight='bold')
    fig.text(.57,.852,"Published projections, expressed without 3D perspective",fontsize=11,color=GRAY)
    ax=fig.add_axes([.61,.555,.32,.258])
    d=projection.loc[projection.outcome=='Major vascular events']
    for rank,g in d.groupby('risk_order',sort=True):
        g=g.sort_values('ldl_reduction_mmol_l');color=PALETTE[int(rank)]
        ax.plot(g.ldl_reduction_mmol_l,g.events_avoided_per_1000_over_5y,color=color,marker='o',lw=2,ms=4.5)
        end=g.iloc[-1]
        ax.text(2.56,end.events_avoided_per_1000_over_5y,end.baseline_5y_major_vascular_risk,color=color,va='center',fontsize=10,weight='bold')
    ax.set(xlim=(.95,2.86),ylim=(0,155),xticks=[1,1.5,2,2.5],xlabel="LDL reduction (mmol/L)",ylabel="Events avoided per 1,000 over five years")
    ax.grid(axis='y',color="#E8EDF0",lw=.8)
    ax.text(.99,.98,"Baseline five-year risk",transform=ax.transAxes,ha='right',va='top',fontsize=9,color=GRAY)
    fig.text(.61,.491,"Model projections for both prevention settings. CTT 2012, Figure 5.",fontsize=9.5,color=GRAY)

    fig.text(.06,.414,"C  First-event prevention and mortality are different outcomes",fontsize=14,weight='bold')
    fig.text(.06,.387,"Primary prevention review; published pooled estimates",fontsize=11,color=GRAY)
    ax=fig.add_axes([.168,.15,.265,.205])
    outcomes=[("Myocardial infarction","Heart attack"),("Stroke","Stroke"),("Composite cardiovascular outcome","Composite CV events"),("All-cause mortality","All-cause mortality"),("Cardiovascular mortality","CV mortality")]
    for i,(name,label) in enumerate(outcomes):
        r=pooled.loc[pooled.endpoint==name].iloc[0];y=4-i
        interval(ax,r.effect,r.ci_low,r.ci_high,y,size=6.5)
        ax.text(1.09,y,f"{r.absolute_risk_reduction_percentage_points*10:g}",transform=ax.get_yaxis_transform(),va='center',ha='center',fontsize=11,weight='bold')
    ax.text(1.09,1.10,"Fewer per\n1,000",transform=ax.transAxes,ha='center',fontsize=9.5,color=GRAY)
    ax.set_yticks(range(5),[label for _,label in outcomes][::-1]);ax.set_ylim(-.6,4.65)
    forest_axis(ax,[.5,.67,.8,1],(.5,1.08))
    ax.set_xlabel("Risk ratio, with 95% confidence interval")
    fig.text(.105,.087,"Observed follow-up differs by trial (1–6 years for these outcomes).",fontsize=9.5,color=GRAY)
    fig.text(.105,.069,"Absolute effects overlap; do not add them. Chou et al., 2022.",fontsize=9.5,color=GRAY)

    fig.text(.57,.414,"D  Similar mortality estimates can yield different certainty",fontsize=14,weight='bold')
    fig.text(.57,.387,"Earlier review, later review, and our independent recalculation",fontsize=11,color=GRAY)
    ax=fig.add_axes([.72,.15,.21,.205])
    r=summary['All-cause mortality']
    comparisons=[("Ray 2010",.91,.83,1.01,GRAY),("USPSTF 2022",.92,.87,.98,GRAY),("Recalculated\n2022 trial counts",r['rr'],r['ci_low'],r['ci_high'],TEAL)]
    for y,(label,rr,lo,hi,color) in zip([2,1,0],comparisons):
        interval(ax,rr,lo,hi,y,color,size=7)
        ax.annotate(f"{rr:.3f} ({lo:.3f}–{hi:.3f})",(rr,y),xytext=(0,-19),textcoords='offset points',ha='center',fontsize=9,color=color)
    ax.set_yticks([2,1,0],[r[0] for r in comparisons]);ax.set_ylim(-.68,2.45)
    forest_axis(ax,[.8,.9,1],(.8,1.04));ax.set_xlabel("All-cause mortality risk ratio (95% CI)")
    fig.text(.61,.087,"Reanalysis: 0.924 (0.868–0.983); heterogeneity I² = 0%.",fontsize=9.5,color=GRAY)
    fig.text(.61,.069,"Overlapping reviews are compared, not pooled together.",fontsize=9.5,color=GRAY)
    fig.text(.06,.018,"A–C redraw published estimates or projections; D includes a new aggregate-data calculation. No individual participant data. The 2022 synthesis is not an update through 2026.",fontsize=9,color=GRAY)
    save_figure(fig,"statins_overview")

def mortality_details(frame,result,loo):
    effects=trial_effects(frame)
    weights=1/(effects.variance+result.tau2);weights=weights/weights.sum()
    fig=plt.figure(figsize=(15.5,10.6))
    fig.text(.06,.962,"Checking the primary prevention mortality result",fontsize=23,weight='bold')
    fig.text(.06,.927,"Recalculated from published arm counts • inverse-variance random effects • normal 95% intervals",fontsize=12,color=GRAY)
    ax=fig.add_axes([.19,.13,.31,.70])
    y_map={index:len(frame)-i for i,index in enumerate(frame.index)}
    for index,row in frame.iterrows():
        y=y_map[index]
        if row.statin_events+row.control_events==0:
            ax.text(.03,y,"No events in either arm",fontsize=9,color=GRAY,va='center')
            continue
        r=effects.loc[index]
        interval(ax,r.rr_recalculated,r.ci_low_recalculated,r.ci_high_recalculated,y,TEAL,marker='s',size=3.3+14*np.sqrt(weights.loc[index]))
    ax.set_yticks([y_map[i] for i in frame.index],[f"{r.trial} ({int(r.year)})" for _,r in frame.iterrows()])
    interval(ax,result.rr,result.ci_low,result.ci_high,0,INK,marker='D',size=9)
    ticks=list(ax.get_yticks())+[0];labels=[t.get_text() for t in ax.get_yticklabels()]+["Pooled estimate"]
    ax.set_yticks(ticks,labels);ax.set_ylim(-1,19)
    forest_axis(ax,[.01,.1,1,10],(.01,40));ax.set_xlabel("Mortality risk ratio (95% CI)")
    fig.text(.06,.869,"A  Individual trials and pooled estimate",fontsize=14,weight='bold')
    ax=fig.add_axes([.705,.13,.24,.70])
    loo=loo.sort_values('rr',ascending=True).reset_index(drop=True)
    for i,r in loo.iterrows():
        interval(ax,r.rr,r.ci_low,r.ci_high,len(loo)-1-i,TEAL,size=5)
    ax.axvline(result.rr,color=TEAL,lw=1,alpha=.5)
    ax.set_yticks(range(len(loo)),[f"Without {r}" for r in loo.omitted_trial][::-1])
    ax.set_ylim(-1,len(loo))
    forest_axis(ax,[.8,.9,1],(.80,1.04));ax.set_xlabel("Recalculated pooled mortality risk ratio")
    fig.text(.59,.869,"B  Leave one contributing trial out",fontsize=14,weight='bold')
    fig.text(.06,.062,f"Pooled RR {result.rr:.3f} ({result.ci_low:.3f}–{result.ci_high:.3f}); {result.trials} contributing estimates from 18 trial rows. Bone et al. contributes no risk-ratio information.",fontsize=10,color=GRAY)
    fig.text(.06,.039,"A 0.5 correction is applied only to a study with a zero-event arm. Omitting trials is exploratory sensitivity analysis, not a new primary analysis.",fontsize=10,color=GRAY)
    fig.text(.06,.016,"Source: Chou et al., JAMA 2022, Figure 3 (PDF page 10). Risk ratios use counts over each trial's follow-up, not reconstructed hazard ratios.",fontsize=9.5,color=GRAY)
    save_figure(fig,"mortality_meta_analysis")

def harms_context():
    muscle=pd.read_csv(DATA/"ctt_2022_muscle_key_rates.csv")
    diabetes=pd.read_csv(DATA/"ctt_2024_diabetes_excess.csv")
    fig=plt.figure(figsize=(13,6.8))
    fig.text(.06,.95,"Adverse effects in their absolute-risk context",fontsize=22,weight='bold')
    fig.text(.06,.90,"Published rounded numbers from CTT analyses; no new pooled harms analysis",fontsize=12,color=GRAY)
    ax=fig.add_axes([.12,.25,.32,.52])
    for i,r in muscle.iterrows():
        y=1-i
        ax.barh(y+.11,r.statin_rate_per_1000_person_years,height=.20,color=ORANGE)
        ax.barh(y-.11,r.placebo_rate_per_1000_person_years,height=.20,color=TEAL)
        ax.text(max(r.statin_rate_per_1000_person_years,r.placebo_rate_per_1000_person_years)+4,y,f"Excess {r.absolute_excess_per_1000_person_years:g}\n({r.excess_ci_low:g} to {r.excess_ci_high:g})",va='center',fontsize=10)
    ax.set(yticks=[1,0],yticklabels=["First year","After year 1"],xlim=(0,222),ylim=(-.55,1.55),xlabel="Reports per 1,000 person-years")
    ax.legend([Line2D([],[],color=ORANGE,lw=7),Line2D([],[],color=TEAL,lw=7)],["Statin","Placebo"],frameon=False,fontsize=10,loc='lower right')
    ax.grid(axis='x',color="#EBEFF1",zorder=0)
    fig.text(.06,.814,"A  Any muscle pain or weakness",fontsize=13,weight='bold')
    ax=fig.add_axes([.62,.25,.32,.52])
    for intensity,color in [("Low/moderate",TEAL),("High",ORANGE)]:
        d=diabetes.loc[(diabetes.statin_intensity==intensity)&(diabetes.classification=='Glycaemia quartile')]
        ax.plot(d.quartile,d.absolute_excess_percentage_points_per_year,'o-',color=color,lw=2,ms=6,label=intensity+" intensity")
        for _,r in d.iterrows():ax.annotate(f"{r.absolute_excess_percentage_points_per_year:.2f}",(r.quartile,r.absolute_excess_percentage_points_per_year),xytext=(0,8),textcoords='offset points',ha='center',fontsize=9,color=color)
    ax.set(xlim=(.8,4.2),ylim=(0,2.05),xticks=[1,2,3,4],xlabel="Baseline glycaemia quartile (lower → higher)",ylabel="Extra diabetes diagnoses (percentage points/year)")
    ax.legend(frameon=False,loc='upper left',fontsize=10);ax.grid(axis='y',color="#EBEFF1")
    fig.text(.56,.814,"B  Estimated excess diabetes diagnoses",fontsize=13,weight='bold')
    fig.text(.06,.143,"A: Symptoms in statin recipients include a large background rate also seen with placebo. Parentheses show 95% intervals for the excess.",fontsize=9.5,color=GRAY)
    fig.text(.06,.111,"B: Published projections assume a constant relative effect within each intensity category. Intensity categories involve different trials and ascertainment.",fontsize=9.5,color=GRAY)
    fig.text(.06,.079,"Both prevention settings contribute. The annual harm rates cannot be subtracted directly from the five-year benefit projections in the overview.",fontsize=9.5,color=GRAY)
    fig.text(.06,.035,"Sources: CTT muscle analysis 2022, Figure 3; CTT diabetes analysis 2024, Figure 2. Lines join published points; they are not fitted regressions.",fontsize=9.5,color=GRAY)
    save_figure(fig,"harms_context")

def main():
    OUT.mkdir(exist_ok=True)
    counts=pd.read_csv(DATA/"uspstf_2022_trial_counts.csv")
    results={};rows=[];trial_tables=[]
    published={"All-cause mortality":(.92,.87,.98),"Cardiovascular mortality":(.91,.81,1.02),"Incident diabetes":(1.04,.92,1.19)}
    for endpoint,d in counts.groupby('outcome',sort=False):
        result=analyze_counts(d)
        results[endpoint]=result.as_dict()
        rows.append({"outcome":endpoint,**result.as_dict(),"published_rr":published[endpoint][0],"published_ci_low":published[endpoint][1],"published_ci_high":published[endpoint][2]})
        e=trial_effects(d);w=1/(e.variance+result.tau2);e['pooled_weight_percent']=100*w/w.sum();trial_tables.append(e)
    pd.DataFrame(rows).to_csv(OUT/"meta_analysis_summary.csv",index=False)
    pd.concat(trial_tables).to_csv(OUT/"trial_effects_recalculated.csv",index=False)
    mortality=counts.loc[counts.outcome=='All-cause mortality']
    sens=sensitivity(mortality);sens.to_csv(OUT/"mortality_sensitivity.csv",index=False)
    loo=leave_one_out(mortality);loo.to_csv(OUT/"mortality_leave_one_out.csv",index=False)
    # Alternative standard pooling and single-zero handling are numerical checks.
    checks=[]
    for method,cc in [('FE',.5),('DL',.5),('DL',.25),('DL',1.)]:
        checks.append({"continuity_correction":cc,**analyze_counts(mortality,method,cc).as_dict()})
    pd.DataFrame(checks).to_csv(OUT/"mortality_method_checks.csv",index=False)
    overview(results)
    mortality_details(mortality,analyze_counts(mortality),loo)
    harms_context()
    metadata={"analysis_date":"2026-10-26","python":platform.python_version(),"versions":{"numpy":np.__version__,"scipy":scipy.__version__,"pandas":pd.__version__,"matplotlib":matplotlib.__version__,"statsmodels":statsmodels.__version__},"results":results,"sensitivity":sens.to_dict(orient='records'),"input_files":[],"output_files":[],"limitations":["Aggregate published counts; no individual participant data.","Reproduction of the 2022 review, not an updated 2026 systematic review.","CTT effect estimates are redrawn, not independently refitted.","Published absolute-benefit and diabetes projections are not observed counts or new regression fits.","Trial effects are not pooled across overlapping reviews or across different endpoints."]}
    for folder,key in [(DATA,"input_files"),(OUT,"output_files")]:
        for path in sorted(folder.glob('*')):
            if path.is_file() and path.name!='results.json':metadata[key].append({"file":str(path.relative_to(ROOT)),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    metadata['code_files']=[{"file":str(path.relative_to(ROOT)),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(BASE.glob('*.py'))]
    lock=BASE/'requirements.lock'
    if lock.exists():metadata['requirements_file']={"file":str(lock.relative_to(ROOT)),"sha256":hashlib.sha256(lock.read_bytes()).hexdigest()}
    (OUT/"results.json").write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+"\n")
    print(pd.DataFrame(rows)[['outcome','trials','rr','ci_low','ci_high','i2_percent']].to_string(index=False))
    print("Saved three figures in PNG, PDF and SVG, plus analysis tables and provenance.")

if __name__=='__main__':main()
