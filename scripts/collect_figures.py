#!/usr/bin/env python3
"""Save original published figures and unmodified PDF pages for close reading."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"figures"
SELECTIONS=[
    ("2012_CTT_low_risk","fig2","01_CTT_2012_figure_2","https://pmc.ncbi.nlm.nih.gov/articles/PMC3437972/#fig2"),
    ("2012_CTT_low_risk","fig5","02_CTT_2012_figure_5","https://pmc.ncbi.nlm.nih.gov/articles/PMC3437972/#fig5"),
    ("2019_CTT_older_people","fig4","06_CTT_2019_figure_4","https://pmc.ncbi.nlm.nih.gov/articles/PMC6429627/#fig4"),
    ("2022_CTT_muscle","fig3","07_CTT_2022_muscle_figure_3","https://pmc.ncbi.nlm.nih.gov/articles/PMC7613583/#fig3"),
    ("2024_CTT_diabetes","F2","08_CTT_2024_diabetes_figure_2","https://pmc.ncbi.nlm.nih.gov/articles/PMC7615958/#F2"),
]

def download(item):
    stem,url,article,caption=item
    response=requests.get(url,timeout=25)
    response.raise_for_status()
    content=response.content
    suffix=".png" if content.startswith(b"\x89PNG\r\n\x1a\n") else ".jpg" if content.startswith(b"\xff\xd8\xff") else ".gif" if content.startswith((b"GIF87a",b"GIF89a")) else None
    if suffix is None: raise ValueError("Not a supported image: "+url)
    path=OUT/(stem+suffix)
    path.write_bytes(content)
    print(path.name, len(content),flush=True)
    return {"file":str(path.relative_to(ROOT)),"source_url":url,"article_url":article,"caption":caption,"retrieved_date":"2026-10-26","sha256":hashlib.sha256(content).hexdigest(),"kind":"original published figure"}

def main():
    OUT.mkdir(exist_ok=True)
    items=[]
    for source,fig_id,stem,article in SELECTIONS:
        soup=BeautifulSoup((ROOT/"papers"/(source+".html")).read_text(),"html.parser")
        figure=soup.find("figure",id=fig_id)
        items.append((stem,figure.find("img")["src"],article,figure.get_text(" ",strip=True)))
    soup=BeautifulSoup((ROOT/"papers/2022_USPSTF_evidence.html").read_text(),"html.parser")
    article="https://www.uspreventiveservicestaskforce.org/uspstf/document/final-evidence-summary/statin-use-in-adults-preventive-medication"
    for number,stem in [(3,"03_USPSTF_2022_figure_3"),(4,"04_USPSTF_2022_figure_4")]:
        img=next(im for im in soup.find_all("img") if im.get("alt","").startswith("Figure "+str(number)+" "))
        items.append((stem,urljoin(article,img["src"]),article,img["alt"]))
    results=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(download,item) for item in items]
        for item,future in zip(items,futures):
            try: results.append(future.result())
            except Exception as exc:
                print("FAILED",item[0],str(exc),flush=True)
                results.append({"source_url":item[1],"error":str(exc)})
    for source,page,stem in [("1995_WOSCOPS",4,"05_WOSCOPS_1995_page_4"),("2022_USPSTF_evidence",10,"03_USPSTF_2022_figure_3_page"),("2022_USPSTF_evidence",15,"04_USPSTF_2022_figure_4_page")]:
        original=ROOT/"papers"/(source+".pdf")
        dest=OUT/(stem+".pdf")
        subprocess.run(["pdfseparate","-f",str(page),"-l",str(page),str(original),str(dest)],check=True,capture_output=True)
        # A page render preserves the printed axes, legends, and surrounding text.
        subprocess.run(["pdftoppm","-f",str(page),"-l",str(page),"-scale-to","2200","-singlefile","-png",str(original),str(OUT/stem)],check=True,capture_output=True)
        for path in [dest,OUT/(stem+".png")]:
            results.append({"file":str(path.relative_to(ROOT)),"source_file":str(original.relative_to(ROOT)),"source_pdf_page":page,"kind":"unmodified PDF page" if path.suffix==".pdf" else "PDF page render","sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    (OUT/"manifest.json").write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n")

if __name__=="__main__": main()
