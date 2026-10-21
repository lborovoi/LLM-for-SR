# LLM screening across three systematic reviews

## Current correction on 21 October 2026

The [reference reconciliation](REFERENCE_RECONCILIATION_2026-10-21.md) supersedes the historical documentation below. Table 1 now uses observed SR1 decision exports. Table 5 uses the identical 28 published final inclusions at every stage; early-stage metrics consequently differ from human intermediate-stage agreement. No individual decisions were changed. Historical aggregate metrics and the previous Table 5 are retained in `results/reference_audit_2026-10-21/`.

## Previous documentation retained for provenance

This repository contains screening code, saved human/model decisions, and results for the manuscript *Validity and consistency of different LLMs in conducting public health systematic reviews: a cautious call for hybrid approaches*.

## Results and manuscript tables

The results correspond to **Final Revised after review, 17 October 2026** and **Supplementary Appendices after review, 17 October 2026**. Different SR1 analyses are identified explicitly.

| File | Contents |
| --- | --- |
| [Table 1](results/manuscript/table1_validity.csv) | Historical SR1 reported matrices, updated one-shot results, and updated SR2/SR3 results (18 rows) |
| [Table 2](results/manuscript/table2_agreement.csv) | Recomputed target-N human–model kappas and separately identified reported paired-subset kappas (9 comparisons) |
| [Table 3](results/manuscript/table3_modern_sr3.csv) | The 2026 SR3 configurations (14 rows) |
| [Table 4](results/manuscript/table4_hybrid_rules.csv) | Record-derived single-model, OR, AND and simulated human-adjudication rules (13 comparisons, 65 rule rows) |
| [Table 5](results/manuscript/table5_additional_sr1.csv) | Additional SR1 decision sets, including the reconstructed Gemini cascade (10 rows) |
| [All manuscript validity results](results/summary_all_models.csv) | Tables 1, 3 and 5, with `manuscript_table`, `analysis_set` and `data_support` fields (42 rows) |
| [Record-derived summary](results/record_level_summary.csv) | All 32 model/stage results reproducible from the three saved decision files |
| [Figure 2 counts](results/manuscript/figure2_counts.csv) | Historical SR1 ChatGPT workflow counts; input and evaluation denominators are separate |

**Historical SR1:** the eight historical matrices in Table 1 are transcribed from the manuscript and its Appendix 2 into [a separate aggregate source](results/reference/sr1_historical_reported.csv). Their metrics are recalculated from those counts. `data_support=reported_aggregate` identifies them: this is arithmetic reproduction of reported results, not verification from individual model decisions. The SR1 records below reproduce Table 5. They must not be relabelled as the historical Table 1 decision set. The source versions and unresolved source differences are recorded in [the provenance file](provenance/analysis_sources.json).

The historical SR1 Gemini full-corpus estimate is **human-gated**: its full-text matrix is expressed on 1,556 records by adding 1,470 upstream reference exclusions as true negatives. It is not an independent autonomous cascade. The additional Gemini reconstruction combines archived upstream decisions with a 2026 full-text stage; it remains a separate analysis.

## Record files and analysis rule

- [SR1](results/sr1_decisions.csv): 1,556 records; human stage-positive totals 496, 86 and 28.
- [SR2](results/sr2_decisions.csv): the recoverable archive of 3,720 records and 74 reference inclusions. The published review included 76 studies.
- [SR3](results/sr3_decisions.csv): 746 records; 101 advanced to full text and **60 final inclusions**. Full-text TF analysis evaluates the 101 records against 60 positives and 41 negatives.

`1` means include and `0` means exclude. **Records without a model inclusion decision are classified as excluded.** In the saved decision files this rule is already applied within each analysis cohort. Blank TF cells identify records outside that human-selected cohort and are not added to its denominator. The files do not preserve the original missing-output flags, so the common observed-decision subsets used for manuscript Table 2 cannot be reconstructed from these binary exports alone.

Historical TF stages receive separate human-selected inputs. Figure 2 therefore does not propagate the TF model inclusions from one stage to the next. Its historical cascade is reported as 1,556 → 608 → 381 → 196; the final 196 equals 28 TP + 168 FP in the reported historical matrix. These aggregate flow totals do not establish a record-by-record linked cascade. The additional one-shot panel evaluates the 1,556-record corpus, with 1,481 PDFs supplied and 362 inclusions (26 TP + 336 FP).

## Reproduce

Python 3.10 or later is sufficient; no model calls or third-party packages are needed.

```bash
python scripts/reproduce_results.py --check
python -m unittest discover -s tests -v
```

To regenerate the result CSVs:

```bash
python scripts/reproduce_results.py
```

The script validates reference totals and nested human cohorts, applies the exclusion rule, calculates TP/FP/FN/TN, Wilson 95% confidence intervals, F1 and human–model Cohen's kappa, and produces the table/figure exports. Table 4 adjudication assumes that a human resolves model disagreements according to the reference decision: it is a retrospective simulation, not measured reviewer performance or time saving. Table 2 preserves its reported common-subset results without inventing observation masks. The script does not select runs by their results or modify individual decisions. Duplicate-looking citations are retained under their saved record IDs.

`summary_all_models.csv` now includes all three manuscript validity tables. Its original 32 record-derived rows are available in `record_level_summary.csv`; use the table and analysis-set fields to select the intended reported result.
