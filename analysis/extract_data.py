#!/usr/bin/env python3
"""Extract aggregate numbers from published figures, with source provenance.

USPSTF event counts are parsed from PDF text. CTT and WOSCOPS values below
are transcriptions of printed numerical labels, not estimates of pixel positions.
No participant records, event times, or unprinted values are reconstructed.
"""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"analysis"
DATA=BASE/"data"

def write_csv(name,rows):
    with (DATA/name).open("w",newline="") as out:
        w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def extract_uspstf():
    destination=BASE/"sources/USPSTF_2022_figure3.txt"
    destination.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(["pdftotext","-f","10","-l","10","-layout",str(ROOT/"papers/2022_USPSTF_evidence.pdf"),str(destination)],check=True)
    text=destination.read_text()
    endpoint=None;rows=[]
    names={"Beishuaizen et al":"Beishuizen et al","ASRONOMER":"ASTRONOMER"}
    for line in text.splitlines():
        if line.strip() in ["All-cause mortality","Cardiovascular mortality","Incident diabetes"]:
            endpoint=line.strip()
        match=re.match(r"^\s*(.+?),(\d+)\s+(\d{4})(a?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.*)$",line)
        if match and endpoint:
            name,ref,year,subgroup,a,n1,c,n0,tail=match.groups()
            effect=re.match(r"([\d.]+)\s*[\(\[]([\d.]+)[-,]\s*([\d.]+)",tail)
            values=list(map(float,effect.groups())) if effect else ["","",""]
            rows.append({"outcome":endpoint,"trial":names.get(name,name),"printed_trial":name,"year":int(year),"primary_prevention_subgroup":bool(subgroup),"statin_events":int(a),"statin_n":int(n1),"control_events":int(c),"control_n":int(n0),"published_rr":values[0],"published_ci_low":values[1],"published_ci_high":values[2],"ci_level":0.95,"source_figure":"USPSTF 2022 Figure 3","source_file":"papers/2022_USPSTF_evidence.pdf","source_pdf_page":10})
    expected={"All-cause mortality":(18,1774,42991,1924,42195),"Cardiovascular mortality":(12,586,37582,645,37556),"Incident diabetes":(6,1004,29536,941,29547)}
    for outcome,counts in expected.items():
        subset=[r for r in rows if r["outcome"]==outcome]
        actual=(len(subset),*(sum(r[key] for r in subset) for key in ["statin_events","statin_n","control_events","control_n"]))
        assert actual==counts,(outcome,actual,counts)
    write_csv("uspstf_2022_trial_counts.csv",rows)

def extract_ctt_risk():
    labels=["<5%","5–<10%","10–<20%","20–<30%","≥30%","All risk groups"]
    groups={
      "No previous vascular disease":[(148,229,.61,.45,.81),(487,716,.66,.57,.77),(854,1003,.82,.72,.93),(294,351,.81,.65,1.01),(121,126,.83,.58,1.18),(1904,2425,.75,.70,.80)],
      "Previous vascular disease":[(19,25,.73,.33,1.61),(117,131,.84,.62,1.14),(2760,3192,.78,.72,.85),(3814,4568,.81,.76,.86),(2666,3332,.79,.74,.84),(9376,11248,.80,.77,.82)],
      "All participants":[(167,254,.62,.47,.81),(604,847,.69,.60,.79),(3614,4195,.79,.74,.85),(4108,4919,.81,.77,.86),(2787,3458,.79,.74,.84),(11280,13673,.79,.77,.81)]}
    rows=[]
    for population,values in groups.items():
        for rank,(label,(a,c,rr,lo,hi)) in enumerate(zip(labels,values)):
            rows.append({"population":population,"risk_category":label,"risk_order":rank,"statin_or_more_events":a,"control_or_less_events":c,"rr_per_1_mmol_ldl":rr,"ci_low":lo,"ci_high":hi,"ci_level":.95 if rank==5 else .99,"is_summary":rank==5,"source_figure":"CTT 2012 Figure 2","source_image":"figures/01_CTT_2012_figure_2.jpg","data_type":"published rounded estimate; not recomputed from event counts"})
    for pop in groups:
        subset=[r for r in rows if r["population"]==pop]
        for key in ["statin_or_more_events","control_or_less_events"]:
            assert sum(r[key] for r in subset if not r["is_summary"])==subset[-1][key],(pop,key)
    write_csv("ctt_2012_risk_effects.csv",rows)

def extract_ctt_projections():
    labels=["<5%","5–<10%","10–<20%","20–<30%","≥30%"]
    outcomes={"Major vascular events":[[6,8,10,12],[15,21,27,31],[31,45,57,68],[45,66,84,100],[61,93,119,142]],
              "Vascular deaths":[[1.2,1.7,2.2,2.7],[4,5,7,8],[8,11,14,17],[11,16,21,25],[20,30,38,46]]}
    rows=[]
    for outcome,values in outcomes.items():
        for rank,(label,points) in enumerate(zip(labels,values)):
            for ldl,avoided in zip([1,1.5,2,2.5],points):
                rows.append({"outcome":outcome,"baseline_5y_major_vascular_risk":label,"risk_order":rank,"ldl_reduction_mmol_l":ldl,"events_avoided_per_1000_over_5y":avoided,"source_figure":"CTT 2012 Figure 5","source_image":"figures/02_CTT_2012_figure_5.jpg","data_type":"published rounded lifetable projection; both prevention settings"})
    write_csv("ctt_2012_absolute_projections.csv",rows)

def extract_other_labels():
    ages=["≤55","56–60","61–65","66–70","71–75",">75","All ages"]
    groups={"No previous vascular disease":[(.68,.56,.83),(.81,.67,.99),(.73,.60,.87),(.61,.51,.73),(.84,.70,1.01),(.92,.73,1.16),(.75,.71,.80)],
            "Previous vascular disease":[(.77,.72,.82),(.78,.73,.82),(.80,.75,.85),(.82,.77,.88),(.80,.74,.88),(.85,.73,.98),(.80,.77,.82)]}
    rows=[]
    for population,values in groups.items():
        for age,(rr,lo,hi) in zip(ages,values):
            rows.append({"population":population,"age_group_years":age,"rr_per_1_mmol_ldl":rr,"ci_low":lo,"ci_high":hi,"ci_level":.95 if age=="All ages" else .99,"source_image":"figures/06_CTT_2019_figure_4.jpg","data_type":"published rounded estimate"})
    write_csv("ctt_2019_age_effects.csv",rows)
    write_csv("ctt_2022_muscle_key_rates.csv",[
        {"period":"Year 1","outcome":"Any muscle pain or weakness","statin_rate_per_1000_person_years":166,"placebo_rate_per_1000_person_years":155,"rate_ratio":1.07,"rr_ci_low":1.04,"rr_ci_high":1.10,"absolute_excess_per_1000_person_years":11,"excess_ci_low":6,"excess_ci_high":16,"source_image":"figures/07_CTT_2022_muscle_figure_3.jpg","data_type":"published rounded rates; not trial event counts"},
        {"period":"After year 1","outcome":"Any muscle pain or weakness","statin_rate_per_1000_person_years":50,"placebo_rate_per_1000_person_years":50,"rate_ratio":.99,"rr_ci_low":.96,"rr_ci_high":1.02,"absolute_excess_per_1000_person_years":0,"excess_ci_low":-2,"excess_ci_high":1,"source_image":"figures/07_CTT_2022_muscle_figure_3.jpg","data_type":"published rounded rates; not trial event counts"}])
    rows=[]
    for intensity,classification,values in [
        ("Low/moderate","Glycaemia quartile",[.06,.07,.16,.48]),("Low/moderate","Predicted diabetes risk quartile",[.03,.08,.17,.57]),
        ("High","Glycaemia quartile",[.23,.27,.59,1.78]),("High","Predicted diabetes risk quartile",[.12,.29,.64,2.11])]:
        for quartile,value in enumerate(values,1):
            rows.append({"statin_intensity":intensity,"classification":classification,"quartile":quartile,"absolute_excess_percentage_points_per_year":value,"source_image":"figures/08_CTT_2024_diabetes_figure_2.jpg","data_type":"published modeled excess assuming constant RR within intensity"})
    write_csv("ctt_2024_diabetes_excess.csv",rows)
    rows=[]
    for arm,events,at_risk in [("Placebo",[0,55,105,159,205,240,248],[3293,3230,3167,3099,2714,1241,83]),("Pravastatin",[0,40,72,109,138,167,174],[3302,3256,3215,3162,2807,1330,99])]:
        for year,(a,n) in enumerate(zip(events,at_risk)):
            rows.append({"arm":arm,"year":year,"cumulative_event_count":a,"number_at_risk":n,"source_figure":"WOSCOPS 1995 Figure 2","source_pdf_page":4,"data_type":"printed counts; not Kaplan–Meier risk estimates or event times"})
    write_csv("woscops_1995_risk_table.csv",rows)

def main():
    DATA.mkdir(parents=True,exist_ok=True)
    extract_uspstf();extract_ctt_risk();extract_ctt_projections();extract_other_labels()
    with (ROOT/"data/review_results.csv").open() as source:
        pooled=[r for r in csv.DictReader(source) if r["source_id"]=="2022_USPSTF_evidence"]
    for row in pooled:
        row["source_figure"]="USPSTF 2022 Figure 4 and abstract"
        row["data_type"]="published pooled estimate; not independently reanalyzed for all endpoints"
    write_csv("uspstf_2022_pooled_outcomes.csv",pooled)
    names=["figures/01_CTT_2012_figure_2.jpg","figures/02_CTT_2012_figure_5.jpg","papers/2022_USPSTF_evidence.pdf","figures/06_CTT_2019_figure_4.jpg","figures/07_CTT_2022_muscle_figure_3.jpg","figures/08_CTT_2024_diabetes_figure_2.jpg","papers/1995_WOSCOPS.pdf"]
    manifest={"extraction_date":"2026-10-26","method":"PDF text parsing for USPSTF Figure 3; transcription of printed numerical labels for other figures; no pixel digitization","sources":[{"file":name,"sha256":hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in names],"csv_files":[]}
    for path in sorted(DATA.glob('*.csv')):
        manifest["csv_files"].append({"file":str(path.relative_to(ROOT)),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    (DATA/"extraction_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("Extracted",len(manifest["csv_files"]),"datasets with source hashes.")

if __name__=="__main__":main()
