# Investigation methods and limits

Research date and evidence cutoff: **26 October 2026**, Europe/Berlin.

## Scope

The question was whether statins provide clinical benefit only after an event such as a heart attack, where that claim may originate, and whether Simpson's paradox explains it. The investigation prioritized randomized trials, primary prevention subgroup analyses, systematic reviews, contemporary guidelines, and the original publications making the skeptical argument.

The literature selection is a focused narrative investigation with an auditable source archive. It is not an exhaustive, preregistered systematic review or a formal risk-of-bias assessment. It does not measure the prevalence of the belief among physicians or identify the source used by a particular physician.

A subsequent [reproducibility analysis](../analysis/README.md) reconstructs three aggregate meta-analyses from the 2022 review's published arm counts and adds sensitivity checks and redrawn figures. It is a reproduction of that evidence set, not a new systematic review or an update through 2026. The statistical methods and accessible-data limits are documented separately there.

## Search approach

Web searches located publisher, PubMed, PMC, university repository, trial investigator, and guideline organization sources. Representative searches included:

- `statins primary prevention all cause mortality systematic review CTT 2012 low risk`
- `Ray 2010 statins all cause mortality 11 randomized trials 65229`
- `Therapeutics Letter 77 2010 statins primary prevention`
- `Abramson 2013 Should people at low risk cardiovascular disease take a statin correction 2014`
- `WOSCOPS AFCAPS TexCAPS JUPITER HOPE-3 original trial`
- `statin older adults ALLHAT PROSPER STAREE 2026 results`
- `statin muscle symptoms 2022 individual participant meta-analysis`
- `statin diabetes 2024 individual participant meta-analysis`
- `2025 ESC EAS dyslipidaemias primary prevention`
- `2026 ACC AHA dyslipidemia primary prevention PREVENT`

References in the historical reviews connected earlier cautious analyses with later summaries. Europe PMC's public API supplied bibliographic records, original abstracts, and XML full text where available. Publisher and official organizational pages were checked against these records. Search snippets were used for discovery; principal trial numbers were checked against downloaded abstracts, full text, or the original indexed abstract. The 2014 correction was checked through the indexed BMJ correction; its original page and PDF could not be saved directly.

## Selection and interpretation

Trials were selected to include early secondary prevention survival evidence, major demonstrations of first-event prevention, neutral results, and older-adult uncertainty. Reviews were selected to reconstruct the disagreement and compare it with later syntheses. The archive intentionally includes critical analyses; inclusion does not endorse every statement in them.

Older trials and reviews do not all use the same primary prevention definition. WOSCOPS excluded prior MI but permitted some other vascular disease; ASCOT excluded coronary disease but permitted some other vascular disease; ALLHAT and PROSPER had mixed populations. Their overall results are not presented as purely primary prevention estimates. The separate clean primary prevention trials address the general claim directly.

Trials recur in different reviews. Their sample sizes must not be added to obtain a total number of independent participants. Evidence reviews, guideline recommendations, critical commentaries, official press releases, and original RCTs have distinct roles and are labeled in the index.

Most of the detailed historical trial reports were not obtainable in full during this run. Abstract-based extraction can establish the stated endpoint and effect estimate but cannot substitute for inspecting all methods, supplements, exclusions, or adjudication procedures. STAREE is represented by its original abstract and an official ESC results release; its full article, protocol and supplement were inaccessible. Older reviews and guideline evidence statements should be read in their own publication context, before STAREE's August 2026 results.

Funding and disclosure information is preserved in full texts and bibliographic records where supplied. Several landmark trials received industry support; the CTT reviews report public or charitable support for their analyses. Sponsorship, early stopping, adherence run-ins, incomplete harms reporting, and restricted access to individual participant data are relevant to appraisal, but are not by themselves evidence that a randomized effect is false. No independent reanalysis of participant-level data was performed. [CTT 2019 disclosures and funding](https://pmc.ncbi.nlm.nih.gov/articles/PMC6429627/), [Cochrane 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC6481400/)

## Extraction and arithmetic

`data/trial_results.csv` records selected trial-level outcomes, arm counts where checked, follow-up, effect measure, and caveats. The reported HR, RR, and OR are preserved as different measures. Simple event proportions and differences are labeled crude calculations; they do not account for censoring or replace the trial's time-to-event estimates. The initial source tables preserve published estimates; they do not recalculate pooled effects.

The later calculations are in `analysis/data/` and `analysis/output/`; they preserve the source's trial subsets and distinguish raw arm counts from published model estimates and projections.

`data/review_results.csv` records review estimates separately. USPSTF absolute differences refer to varying trial durations, not a common five-year horizon. Its evidence report gives the myocardial infarction absolute difference as 0.85 percentage points; its recommendation page gives 0.89. The overview consistently uses the evidence report's 0.85. Endpoint-specific samples differ, and overlapping events must not be added.

`data/absolute_risk_examples.csv` and `data/simpson_example.csv` contain invented arithmetic examples, explicitly separated from evidence. The assumed 20% relative reduction is used to explain a calculation, not to predict an individual's response. The Simpson example changes the distribution of baseline risk between treatment groups; it is not evidence of such a reversal in the statin RCTs.

## Archive and reproducibility

The manifest records source URLs, retrieval date, failed attempts, file sizes, and SHA-256 hashes. PDFs are accepted only when their bytes start with the PDF signature. `pdftotext` creates searchable local text copies. HTML and XML originals remain in `papers/`. Full-text HTML may require an internet connection for figures or styling; the extracted text can be read offline.

The WOSCOPS PDF comes from a public personal mirror, with the original journal title and DOI checked against the bibliographic record. The Abramson PDF is a journal reprint hosted by a Catalan primary care public health program. The index preserves these download locations separately from canonical publication links. The original Abramson PDF contains the subsequently corrected adverse-effect claims. The HOPE-3 alternative, if successfully retrieved, is a university repository copy.

The source index distinguishes full text from abstracts or bibliographic records. A guideline announcement or official results release is a supporting source, not a substitute for the complete guideline or trial paper. No paywalls, login requirements, or browser challenges were bypassed.

To rebuild using Python 3, `requests`, `beautifulsoup4`, and the system `pdftotext` utility:

```bash
python3 scripts/download_sources.py
python3 scripts/enrich_sources.py
python3 scripts/add_public_copies.py
python3 scripts/build_index.py
```

URLs and access permissions can change. Successful retrieval in this archive does not imply permission to redistribute copyrighted papers. Downloaded copies retain their original copyright notices.
