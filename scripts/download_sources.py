#!/usr/bin/env python3
"""Archive public research sources; preserve failures and never save HTML as PDF.

Requires requests and beautifulsoup4; PDF extraction uses pdftotext if installed.
Reruns keep successful files and retry missing resources. No login or CAPTCHA handling.
"""
import concurrent.futures
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCES = json.loads((ROOT / "data/sources.json").read_text())
DATE = "2026-10-26"
manifest_path = ROOT / "data/download_manifest.json"
PREVIOUS_FILES = {
    f["path"]: f
    for record in (json.loads(manifest_path.read_text()) if manifest_path.exists() else [])
    for f in record["files"]
}

def fetch_one(source):
    sid = source["id"]
    files, attempts = [], []
    urls = [(u, "pdf") for u in source.get("pdf_urls", [])]
    urls += [(source["url"], "fulltext" if source.get("fulltext") else "record")]
    urls += [(u, "record") for u in source.get("additional_urls", [])]
    seen = set()
    pdf_found = False
    fulltext_found = False
    while urls:
        url, kind = urls.pop(0)
        if url in seen or (kind == "pdf" and pdf_found):
            continue
        seen.add(url)
        if kind == "pdf":
            path = ROOT / "papers" / (sid + ".pdf")
        else:
            path = ROOT / "papers" / (sid + ("_record" if kind == "record" else "") + ".html")
        if path.exists():
            payload = path.read_bytes()
            attempts.append({"url": url, "status": "existing", "file": str(path.relative_to(ROOT))})
        else:
            try:
                response = requests.get(url, timeout=25, headers={"User-Agent": "StatinEvidenceResearch/1.0 (public literature archive)"})
                payload = response.content
                a = {"url": url, "final_url": response.url, "status": response.status_code, "bytes": len(payload)}
                attempts.append(a)
                if response.status_code != 200:
                    continue
                if kind == "pdf":
                    if not payload.startswith(b"%PDF-"):
                        a["error"] = "Not a PDF; not saved"
                        continue
                else:
                    soup = BeautifulSoup(payload, "html.parser")
                    title = soup.title.get_text(" ",strip=True) if soup.title else ""
                    if any(x in title.lower() for x in ["captcha", "just a moment", "access denied", "checking your browser"]):
                        a["error"] = "Browser challenge; not saved"
                        continue
                    if len(soup.get_text(" ",strip=True)) < 600:
                        a["error"] = "Insufficient source content; not saved"
                        continue
                path.write_bytes(payload)
                a["file"] = str(path.relative_to(ROOT))
            except requests.RequestException as exc:
                attempts.append({"url": url, "error": str(exc)})
                continue
        rel = str(path.relative_to(ROOT))
        digest = hashlib.sha256(payload).hexdigest()
        old = PREVIOUS_FILES.get(rel,{})
        provenance_url = old.get("source_url",url) if old.get("sha256")==digest else url
        files.append({"path": rel, "kind": kind, "sha256": digest, "bytes": len(payload), "source_url": provenance_url})
        if kind == "pdf":
            pdf_found = True
            dest = ROOT / "text" / (sid + ".txt")
            result = subprocess.run(["pdftotext", "-layout", str(path), str(dest)], capture_output=True)
            if result.returncode:
                attempts.append({"error": "pdftotext failed", "file": rel})
        else:
            soup = BeautifulSoup(payload, "html.parser")
            if kind == "fulltext":
                # A page with an abstract alone is never called full text.
                article = soup.find("article") or soup.find("main") or soup
                raw = article.get_text(" ",strip=True).lower()
                fulltext_found = bool(re.search(r"\b(methods|methodology)\b", raw) and re.search(r"\b(discussion|recommendation|conclusion)\b", raw))
                if "release" in source["type"] or "recommendation" in source["type"]:
                    fulltext_found = True
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            (ROOT / "text" / (path.stem + ".txt")).write_text(soup.get_text("\n",strip=True))
            for a in soup.find_all("a",href=True):
                href = a["href"]
                label = a.get_text(" ",strip=True).lower()
                if ("pdf" in href.lower() and "supp" not in href.lower() and "/bin/" not in href.lower() and (label == "pdf" or "download pdf" in label)) or "download evidence summary" in label:
                    urls.append((urljoin(url, href), "pdf"))
    status = "full text PDF" if pdf_found else "full text HTML" if fulltext_found else "record or abstract only" if files else "not downloaded"
    print(sid + ": " + status, flush=True)
    return {**source, "retrieved_date": DATE, "status": status, "files": files, "attempts": attempts}

def main():
    for folder in ["papers", "text", "data"]:
        (ROOT / folder).mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(fetch_one, SOURCES))
    (ROOT / "data/download_manifest.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    with (ROOT / "data/source_index.csv").open("w", newline="") as out:
        fields = ["id", "type", "title", "doi", "url", "status", "local_files", "retrieved_date"]
        writer = csv.DictWriter(out,fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({**{f:r.get(f,"") for f in fields if f != "local_files"}, "local_files":"; ".join(f["path"] for f in r["files"])})
    counts = {s:sum(r["status"] == s for r in results) for s in sorted({r["status"] for r in results})}
    print(json.dumps(counts))

if __name__ == "__main__":
    main()
