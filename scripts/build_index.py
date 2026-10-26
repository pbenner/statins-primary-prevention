#!/usr/bin/env python3
"""Build the source index and transparent arithmetic tables; verify file hashes."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def write_csv(name,rows):
    with (ROOT/"data"/name).open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

def main():
    manifest=json.loads((ROOT/"data/download_manifest.json").read_text())
    crossref=ROOT/"data/2014_Abramson_correction_crossref.json"
    if crossref.exists():
        r=next(r for r in manifest if r["id"]=="2014_Abramson_correction")
        payload=crossref.read_bytes(); path=str(crossref.relative_to(ROOT))
        if not any(f["path"]==path for f in r["files"]):
            r["files"].append({"path":path,"kind":"bibliographic record","bytes":len(payload),"sha256":hashlib.sha256(payload).hexdigest(),"source_url":"https://api.crossref.org/works/10.1136/bmj.g3329"})
        if r["status"]=="not downloaded": r["status"]="record or abstract only"
    for r in manifest:
        for f in r["files"]:
            p=ROOT/f["path"]
            assert p.exists(), str(p)
            assert hashlib.sha256(p.read_bytes()).hexdigest()==f["sha256"],str(p)
    (ROOT/"data/download_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    counts={s:sum(r["status"]==s for r in manifest) for s in sorted({r["status"] for r in manifest})}
    lines=["# Statin research source index","","Retrieved 26 October 2026. Each entry identifies the publication, evidence type, canonical link, local files, and access status.","",
           "Full text includes trial reports, reviews, critical bulletins, recommendations and official releases; see each evidence type. Records or abstracts do not imply that the complete paper was downloaded.","",
           "Archive status: "+"; ".join(str(n)+" "+s for s,n in counts.items())+".","",
           "**Read the original 2013 Abramson article together with the [2014 correction](https://www.bmj.com/content/348/bmj.g3329).** Its original adverse-effect estimates were corrected.",""]
    index=[]
    for r in manifest:
        lines.extend(["## "+r["id"].replace("_"," "),"",r["title"],"", "Type: "+r["type"]+". Access: **"+r["status"]+"**.",""])
        links=["[Publication]("+r["url"]+")"]
        if r.get("doi"): links.append("[DOI](https://doi.org/"+r["doi"]+")")
        lines.extend([" · ".join(links),""])
        for f in r["files"]:
            lines.append("- ["+f["kind"]+" — "+f["path"]+"]("+f["path"]+")")
            if f["kind"]=="pdf": lines.append("  Download source: [public copy]("+f["source_url"]+").")
        if not r["files"]: lines.append("No original file obtained; use the publication link.")
        if r["status"]=="record or abstract only":
            lines.extend(["","The complete publication was not obtained. Any saved organizational page may be an extract or summary rather than the full guideline."])
        lines.append("")
        index.append({**{k:r.get(k,"") for k in ["id","type","title","doi","url","status","retrieved_date"]},"local_files":"; ".join(f["path"] for f in r["files"])})
    (ROOT/"STUDY_INDEX.md").write_text("\n".join(lines))
    write_csv("source_index.csv",index)
    with (ROOT/"references.bib").open("w") as out:
        for r in manifest:
            kind="article" if r.get("doi") else "misc"
            out.write("@"+kind+"{"+r["id"]+",\n")
            for k,v in {"title":r["title"],"year":r["id"][:4],"doi":r.get("doi"),"url":r["url"],"note":r["type"]+"; accessed 2026-10-26"}.items():
                if v: out.write("  "+k+" = {"+v.replace("&",r"\&")+"},\n")
            out.write("}\n\n")
    examples=[]
    for risk in [0.01,0.05,0.10,0.20]:
        treated=risk*0.8; arr=risk-treated
        examples.append({"data_type":"illustrative assumption, not study data","followup_years":5,"untreated_risk":risk,"assumed_rr":0.8,"treated_risk":round(treated,6),"absolute_risk_reduction":round(arr,6),"prevented_per_1000":round(arr*1000,3),"nnt":round(1/arr)})
    write_csv("absolute_risk_examples.csv",examples)
    simpson=[{"data_type":"invented example, not study data","risk_group":"lower","statin_events":8,"statin_n":1000,"control_events":90,"control_n":9000},
             {"data_type":"invented example, not study data","risk_group":"higher","statin_events":720,"statin_n":9000,"control_events":100,"control_n":1000}]
    assert all(abs((r["statin_events"]/r["statin_n"])/(r["control_events"]/r["control_n"])-0.8)<1e-12 for r in simpson)
    simpson.append({"data_type":"invented example, not study data","risk_group":"pooled","statin_events":728,"statin_n":10000,"control_events":190,"control_n":10000})
    write_csv("simpson_example.csv",simpson)
    print(json.dumps(counts)); print("Verified "+str(sum(len(r["files"]) for r in manifest))+" archived file hashes.")

if __name__=="__main__": main()
