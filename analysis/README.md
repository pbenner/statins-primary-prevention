# Statin figure data and reproducible analysis

**Published aggregate numbers are available, and the 2022 review can be checked from its printed trial counts.** Individual participant data are a different matter: CTT does not release the pooled patient dataset; requests must go to the contributing trial custodians. Its policy also allows researchers to propose analyses to the collaboration. [CTT data policy](https://www.cttcollaboration.org/about2)

The overview figure (`output/statins_overview.pdf`, generated locally) combines redrawn published results with an independent aggregate-data calculation. The extraction script generates eight CSV files under `analysis/data/`. A mortality forest plot and leave-one-out analysis (`output/mortality_meta_analysis.pdf`, generated locally) and a harms figure (`output/harms_context.pdf`, generated locally) provide additional detail. Every figure is available as PNG, PDF and editable SVG in output/ (`output/`, generated locally).

The [notebook](statins_overview.ipynb) provides a shorter walkthrough with all three figures, source notes and recalculation cells. After extracting the inputs, select the project's `.venv/bin/python` kernel to run it. Notebook dependencies are listed in [requirements-notebook.txt](requirements-notebook.txt); its exports go to `analysis/notebook_output/`.

![Overview of statin effects and mortality reanalysis](../figures/statins_overview.png)

The repository keeps the notebook source and the README figure assets, while
source downloads, extracted datasets, execution outputs, and other exports are
ignored. Paths to those files below become available after rebuilding locally.
See the [root README](../README.md#reproduce-the-figures) for the complete setup.

## What data were obtained

| Original figures | Local numerical data | What can be done with them |
| --- | --- | --- |
| CTT 2012 Figure 2 | Risk-stratum effects (`data/ctt_2012_risk_effects.csv`, generated locally), including rounded rate ratios, confidence limits and event counts | Redraw the forest plot. Individual strata use 99% intervals and summaries use 95%. Counts alone cannot reproduce the LDL-adjusted participant-level estimates. |
| CTT 2012 Figure 5 | Absolute-benefit projections (`data/ctt_2012_absolute_projections.csv`, generated locally) | Redraw the printed lifetable projections in two dimensions. They are model outputs, not raw outcomes or independent observations for a new regression. |
| USPSTF 2022 Figure 3 | Trial arm counts (`data/uspstf_2022_trial_counts.csv`, generated locally) for mortality, cardiovascular mortality and diabetes | Recalculate risk ratios and repeat aggregate meta-analysis. The source supplies 36 trial-outcome rows, including 18 mortality rows. |
| USPSTF 2022 Figure 4 | Published pooled benefit estimates (`data/uspstf_2022_pooled_outcomes.csv`, generated locally) | Redraw the main benefit outcomes. MI, stroke and composite results here are published estimates, not independently recalculated trial-level analyses. |
| WOSCOPS Figure 2 | Numbers at risk and cumulative event counts (`data/woscops_1995_risk_table.csv`, generated locally) | Inspect the follow-up table. These numbers do not identify individual event or censoring times and cannot recreate the exact Kaplan–Meier curves or Cox model. |
| CTT 2019 Figure 4 | Age-group effect estimates (`data/ctt_2019_age_effects.csv`, generated locally) | Redraw the age subgroup plot. These results predate STAREE 2026. |
| CTT muscle analysis 2022 Figure 3 | Key symptom rates and treatment excess (`data/ctt_2022_muscle_key_rates.csv`, generated locally) | Compare background rates with excess rates, separating year 1 from later years. These are rounded rates, not counts of unique patients. |
| CTT diabetes analysis 2024 Figure 2 | Printed excess estimates (`data/ctt_2024_diabetes_excess.csv`, generated locally) | Redraw the modeled excess by baseline risk. It assumes a constant relative effect within each intensity category. |

Sources: [CTT 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3437972/), [USPSTF 2022](https://doi.org/10.1001/jama.2022.12138), [WOSCOPS](https://doi.org/10.1056/NEJM199511163332001), [CTT 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6429627/), [muscle analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC7613583/), [diabetes analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC7615958/).

The CTT and WOSCOPS numbers were transcribed from printed numerical labels; curve heights were not digitized. USPSTF Figure 3 was parsed from the downloaded PDF's text, and all arm totals were checked against its printed totals. The extraction manifest (`data/extraction_manifest.json`, generated locally) identifies source files and hashes. Some datasets contain nested summaries or repeated outcomes and are **not independent datasets that can be pooled together**.

AHRQ also lists a public **Project Data XLSX workbook** for this review. Its page returned a browser challenge or empty response here, so the workbook was **not downloaded or used**. Attempts to retrieve supplementary PDFs and the complete Bookshelf report also failed content validation. Those failures are recorded in download_attempts.json (`sources/download_attempts.json`, generated locally). The extracted datasets above come from the original files already obtained, not from the inaccessible workbook. [AHRQ dataset listing](https://effectivehealthcare.ahrq.gov/srdrplus/statin-use-primary-prevention-cardiovascular-disease-adults-preventive-medication)

## What was recalculated

The three analyses below use the arm-level counts in USPSTF Figure 3, over the follow-up used in that review. They reproduce the published risk ratios and confidence limits when rounded to two decimal places. Intermediate heterogeneity statistics differ slightly from the printed values; this is a transparent reconstruction, not an exact replay of the authors' software session.

| Endpoint | Contributing estimates | Recalculated RR and 95% CI | Published RR and 95% CI | Recalculated I² |
| --- | --- | --- | --- | --- |
| All-cause mortality | 17 | **0.924 (0.868–0.983)** | 0.92 (0.87–0.98) | 0% |
| Cardiovascular mortality | 12 | **0.910 (0.815–1.016)** | 0.91 (0.81–1.02) | 0% |
| Incident diabetes | 6 | **1.044 (0.916–1.190)** | 1.04 (0.92–1.19) | 51.5% |

The mortality source includes 18 trial rows and 85,186 participants. Bone et al. had no deaths in either arm and supplies no information for a risk ratio, leaving 17 contributing estimates. The source's trial subsets are preserved; the `primary_prevention_subgroup` flag records its footnote, not a classification of all other trials as secondary prevention. Years are those printed in the source and may refer to a subgroup report rather than the original trial.

The diabetes calculation reproduces a **2022 primary prevention review**. It does not supersede the larger 2024 CTT diabetes analysis. Similarly, none of these calculations updates the systematic review through 2026. In particular, STAREE's disability-free survival composite cannot be substituted for an all-cause mortality count.

### Statistical method

For trial i, the analysis calculates

```text
log(RR_i) = log(a_i / n_statin_i) - log(c_i / n_control_i)
var_i = 1/a_i - 1/n_statin_i + 1/c_i - 1/n_control_i
```

Here `a` and `c` are events, and `n` is the corresponding randomized arm total used by the source. A study with zero events in one arm receives a 0.5 correction to **all four cells of that study**, increasing each arm denominator by 1. The correction is not applied to every study. Double-zero studies are omitted from risk-ratio pooling.

The primary reconstruction uses inverse-variance random effects with the DerSimonian–Laird estimate of between-trial variance, bounded at zero. It reports conventional normal 95% intervals. Common-effect pooling and alternative continuity corrections are saved in mortality_method_checks.csv (`output/mortality_method_checks.csv`, generated locally). These count-based risk ratios do not reconstruct time-to-event hazard ratios or unequal censoring within a trial.

Seven numerical checks verify printed totals, subgroup interval levels, zero handling, arm-swap reciprocity, agreement with an independent statistical implementation, and reproduction of the published rounded estimates. The independent checks use [Statsmodels' meta-analysis implementation](https://www.statsmodels.org/stable/_modules/statsmodels/stats/meta_analysis.html). Its untruncated DerSimonian–Laird estimator is handled explicitly when negative; the primary analysis bounds variance at zero.

## Sensitivity to trial selection

These checks help explain disagreement between reviews. They are exploratory and change the selected evidence; they do not establish which selection is correct.

| Mortality analysis | RR and 95% CI |
| --- | --- |
| All eligible trials | **0.924 (0.868–0.983)** |
| Exclude ALLHAT-LLT | **0.892 (0.827–0.962)** |
| Exclude JUPITER | **0.941 (0.880–1.005)** |
| Exclude ASCOT-LLA, CARDS and JUPITER, three trials stopped early | **0.963 (0.896–1.036)** |
| Exclude ALLHAT-LLT and PROSPER | **0.871 (0.804–0.944)** |

The full trial-level calculation supports a small mortality reduction. Omitting JUPITER moves the interval across 1, while omitting ALLHAT makes the estimate more favorable. Neither calculation reverses the point estimate to harm. Excluding early-stopped trials is a sensitivity check on that concern, not proof that their effects are biased: it also removes substantial randomized information from selected populations. The leave-one-out figure (`output/mortality_meta_analysis.pdf`, generated locally) shows the effect of each individual omission.

A significance threshold can therefore change with trial selection while point estimates remain compatible. This supports the original explanation involving precision and study selection rather than demonstrating Simpson's paradox. It also leaves the separate evidence for preventing nonfatal events intact.

## What the overview figure means

Panel A redraws CTT's published risk-stratum estimates, preserving the 99% and 95% interval distinction. Panel B redraws its five-year absolute-benefit projections. Panel C shows published primary prevention benefit estimates over varying trial follow-up. Panel D compares the historical mortality estimates with our recalculation. **Panels A–C are not new fits of the original participant data.**

Lines in Panel B join the published projection values. The printed figure does not supply the parameter covariance needed to calculate a new uncertainty band, so none is invented.

The harms figure likewise redraws published rates and projections. Its intensity groups come from different trial sets and diabetes ascertainment practices; they do not form a direct randomized comparison between doses. Annual harms and five-year benefits must not be subtracted from one another as if they had a common time horizon, population and clinical severity.

## Why no new regression was fitted

A regression through the five CTT risk categories would treat coarse categories as if their exact baseline risks and covariance were known. They are not. The open-ended ≥30% category has no defensible numerical midpoint. A regression of treatment RR against observed control-arm event risk would also reuse the control outcome on both axes, creating mathematical coupling. These approaches would not establish a patient-level interaction or resolve Simpson's paradox.

For the present question, stratified forest plots, an aggregate meta-analysis, and sensitivity checks answer more directly what the accessible data support. Patient-level regression by baseline risk, prior disease, age or LDL reduction would require the trial data and the original modeling details. A future trial-level meta-regression with independently extracted study characteristics could be exploratory, but cannot replace a participant-level interaction analysis.

## Reproduce the analysis

The required analysis packages are pinned in [requirements.lock](requirements.lock). `pdftotext` is also needed to regenerate the extracted USPSTF table. For a fresh checkout, first follow the [source retrieval and extraction steps](../README.md#reproduce-the-figures). Generated data and outputs are not versioned.

```bash
# Run from the project root with the existing environment
.venv/bin/python analysis/extract_data.py
.venv/bin/python analysis/test_analysis.py
.venv/bin/python analysis/run_analysis.py
```

To create a fresh environment using a system pip that supports `--python`:

```bash
python3 -m venv --without-pip .venv
python3 -m pip --python .venv/bin/python install -r analysis/requirements.lock
```

The run saves numerical results, package versions, input hashes and output hashes in results.json (`output/results.json`, generated locally). Figure captions identify the source and interpretation limits. The PNG is for preview, the PDF for sharing or printing, and the SVG for editing the layout. Refresh the README assets separately as described in the root README.
