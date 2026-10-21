# SR1 reconciliation against the same 28 published studies

Final reference is identified from Essa-Hadad et al., DOI 10.1093/eurpub/ckad232, Table 1 and Supplements III/IV. The [manifest](results/reference_audit_2026-10-21/published_28_reference.csv) contains publication reference number, record ID, title and DOI. It includes Greenfield 2015, and excludes Pratt 2019 and Zibrik 2018. Another archived list totalled 28 but contained Pratt instead of Greenfield.

Table 1 now uses observed record-level SR1 decisions. Early-stage reference outcomes are the human title/abstract gates (496 and 86), and final outcomes use the published 28. Earlier aggregate-only matrices are retained in `historical_aggregate_metrics.csv`, not primary estimates. All original model decisions and original aggregate inputs remain unchanged.

Table 5 instead uses **final inclusion as the reference at every stage**. All 28 final positives belong to each TF cohort. ChatGPT title sensitivity is 28/28 (100%) and abstract sensitivity 27/28 (96.4%); these differ from intermediate-stage agreement of 218/496 (44%) and 72/86 (83.7%). Specificity, PPV, F1 and kappa were also recalculated against final inclusion. Old Table 5 is archived as `table5_previous_stage_references.csv`. Tables 2 and 4 retain stage-specific references matching Table 1.

The observed ChatGPT nTF set remains **20/28**. All 198 inclusions match the original `198_with_final28_marked.xlsx`; the eight absent final studies are absent after DOI/title checks too. Another master contains upstream INCLUDE decisions for them, but those cannot be substituted into another observed final-membership run. A reconstruction using separate TF stages is not an observed autonomous experiment. The original 198-file column `Included_in_Final28` is false in every row and was not used as the reference.

The [28-study trace](results/reference_audit_2026-10-21/published_28_stage_trace.csv) exposes every comparison. Source hashes identify inspected archives. The full master maps uniquely to all 1,556 current records; one additional PD-L1 record is outside that corpus. September v4 differs by one irrelevant record and has two similarly titled PD-L1 records; row-order joins and ambiguous title joins were not used to replace decisions. September v4 columns are comparison evidence, not verified original outputs.

Figure 2 now gives independent TF input/output counts, the separate observed nTF endpoint, and one-shot screening. Intermediate nTF totals are not inferred from unrelated stage columns.

Binary exports still lack observation masks for the reported paired-subset agreement statistics. Original paired inter-model/Fleiss estimates remain labelled as reported; this correction does not establish their independent reproduction. Missing inclusion decisions remain exclusions within target cohorts. None of the changes requires model calls.
