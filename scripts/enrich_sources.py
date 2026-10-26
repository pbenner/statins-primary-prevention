#!/usr/bin/env python3
"""Add Europe PMC bibliographic records, abstracts, XML and openly linked PDFs.

Run after download_sources.py. Earlier download attempts are retained.
"""
import concurrent.futures
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/"

def add_file(record, path, content, kind, url):
    path.write_bytes(content)
    rel = str(path.relative_to(ROOT))
    record["files"] = [f for f in record["files"] if f["path"] != rel]
    record["files"].append({"path":rel, "kind":kind, "bytes":len(content), "sha256":hashlib.sha256(content).hexdigest(), "source_url":url})

def enrich(r):
    sid = r["id"]
    if not r.get("doi"):
        return r
    query = 'DOI:"' + r["doi"] + '"'
    try:
        response = requests.get(BASE + "search", params={"query":query,"format":"json","resultType":"core"}, timeout=20)
        response.raise_for_status()
        results = response.json().get("resultList",{}).get("result",[])
        matches = [x for x in results if x.get("doi", "").lower() == r["doi"].lower()]
        if not matches and r.get("pmid"):
            response = requests.get(BASE+"search",params={"query":"EXT_ID:"+r["pmid"]+" AND SRC:MED","format":"json","resultType":"core"},timeout=20)
            response.raise_for_status()
            matches = [x for x in response.json().get("resultList",{}).get("result",[]) if x.get("id")==r["pmid"]]
        if not matches:
            r["attempts"].append({"url":response.url,"status":"no matching Europe PMC DOI record"})
            return r
        m = matches[0]
        add_file(r,ROOT/"data"/(sid+"_bibliography.json"),json.dumps(m,indent=2,ensure_ascii=False).encode(),"bibliographic record",response.url)
        if r["status"] == "not downloaded":
            r["status"] = "record or abstract only"
        r["verified_title"] = m.get("title")
        r["authors"] = m.get("authorString", "")
        r["pmid"] = m.get("id",r.get("pmid", ""))
        abstract = m.get("abstractText")
        if abstract:
            abstract_text = BeautifulSoup(abstract,"html.parser").get_text("\n",strip=True)
            text = m.get("title",r["title"])+"\n"+r["doi"]+"\nSOURCE: "+response.url+"\n\nABSTRACT ONLY\n\n"+abstract_text+"\n"
            add_file(r,ROOT/"text"/(sid+"_abstract.txt"),text.encode(),"abstract",response.url)
            if r["status"] == "not downloaded":
                r["status"] = "record or abstract only"
        pmcid = m.get("pmcid") or r.get("pmcid")
        if pmcid:
            xml_url = BASE+pmcid+"/fullTextXML"
            xr = requests.get(xml_url,timeout=20)
            a = {"url":xml_url,"status":xr.status_code}
            r["attempts"].append(a)
            if xr.status_code == 200 and b"<article" in xr.content:
                add_file(r,ROOT/"papers"/(sid+".xml"),xr.content,"fulltext XML",xml_url)
                if r["status"] not in ["full text PDF", "full text HTML"]:
                    r["status"] = "full text XML"
        if r["status"] != "full text PDF":
            candidates = [x["url"] for x in m.get("fullTextUrlList",{}).get("fullTextUrl",[]) if x.get("availabilityCode")=="F" and x.get("documentStyle")=="pdf"]
            for pdf_url in dict.fromkeys(candidates):
                pr = requests.get(pdf_url,timeout=20)
                a = {"url":pdf_url,"final_url":pr.url,"status":pr.status_code}
                r["attempts"].append(a)
                if pr.status_code==200 and pr.content.startswith(b"%PDF-"):
                    path = ROOT/"papers"/(sid+".pdf")
                    add_file(r,path,pr.content,"pdf",pdf_url)
                    subprocess.run(["pdftotext","-layout",str(path),str(ROOT/"text"/(sid+".txt"))],capture_output=True,check=True)
                    r["status"]="full text PDF"
                    break
    except (requests.RequestException,ValueError,subprocess.SubprocessError) as exc:
        r["attempts"].append({"stage":"Europe PMC enrichment","error":str(exc)})
    print(sid+": "+r["status"],flush=True)
    return r

def main():
    results = json.loads((ROOT/"data/download_manifest.json").read_text())
    existing = {r["id"] for r in results}
    for source in json.loads((ROOT/"data/sources.json").read_text()):
        if source["id"] not in existing:
            results.append({**source,"retrieved_date":"2026-10-26","status":"not downloaded","files":[],"attempts":[]})
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(enrich,results))
    (ROOT/"data/download_manifest.json").write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n")
    with (ROOT/"data/source_index.csv").open("w",newline="") as out:
        fields=["id","type","title","doi","url","status","local_files","retrieved_date"]
        writer=csv.DictWriter(out,fieldnames=fields); writer.writeheader()
        for r in results:
            writer.writerow({**{f:r.get(f,"") for f in fields if f!="local_files"},"local_files":"; ".join(f["path"] for f in r["files"])})
    print({s:sum(r["status"]==s for r in results) for s in sorted({r["status"] for r in results})})

if __name__=="__main__":
    main()
