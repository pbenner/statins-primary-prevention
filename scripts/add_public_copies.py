#!/usr/bin/env python3
"""Fetch additional public copies discovered during the investigation.

Uses the same validation, extraction and provenance helpers as the main scripts.
"""
import json
from download_sources import fetch_one
from enrich_sources import ROOT

EXTRAS = {
    "1995_WOSCOPS": {"pdf_urls":["https://r.jordan.im/download/cholesterol/shepherd1995.pdf"]},
    "2013_Abramson_BMJ": {"pdf_urls":["https://gestor.papsf.cat/_Adm3/upload/docs/ITEMDOC_1768.pdf"]},
    "2016_HOPE3": {"pdf_urls":["https://irep.iium.edu.my/50353/7/Cholesterol_Lowering_in_Intermediate-Risk.pdf"]},
    "2010_Ray_mortality": {"url":"https://eprints.gla.ac.uk/39606/"},
    "2025_ESC_EAS_guideline": {"fulltext":True},
    "2023_NICE_NG238": {"fulltext":True},
}

def main():
    manifest = json.loads((ROOT/"data/download_manifest.json").read_text())
    sources = {r["id"]:r for r in json.loads((ROOT/"data/sources.json").read_text())}
    for record in manifest:
        sid=record["id"]
        if sid not in EXTRAS:
            continue
        source={**sources[sid],**EXTRAS[sid]}
        # Keep canonical source URL and bibliography; merge acquired copies only.
        more=fetch_one(source)
        paths={f["path"] for f in record["files"]}
        record["files"].extend(f for f in more["files"] if f["path"] not in paths)
        record["attempts"].extend(more["attempts"])
        if more["status"].startswith("full text"):
            record["status"]=more["status"]
        elif record["status"]=="not downloaded" and more["files"]:
            record["status"]=more["status"]
    (ROOT/"data/download_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")

if __name__=="__main__":
    main()
