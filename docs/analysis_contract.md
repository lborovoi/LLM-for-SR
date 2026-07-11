# Locked analysis contract

## Reference standard

Human review decisions are the reference standard. `1` means include and `0`
means exclude. Model decisions use the same coding.

## Traditional-flow endpoints

- SR1 title screening uses all 1,556 records.
- SR1 title/abstract screening is evaluated only among the 496 records that
  passed human title screening.
- SR1 full-text screening is evaluated only among the 86 records that passed
  human title/abstract screening.
- SR3 title/abstract screening uses all 746 records.
- SR3 full-text screening is evaluated only among the 101 records that passed
  human title/abstract screening.

These are human-gated stage-specific validity analyses. They are not the same
as an end-to-end autonomous pipeline.

## Non-traditional-flow endpoint

The nTF endpoint is evaluated across the full starting universe. A record is
included only if the model includes it at every required model stage. This
captures cumulative loss and cumulative workload in a single final decision.

## Missing output rule

A missing or failed model output is retained in a dedicated flag and treated
as `EXCLUDE` in the primary end-to-end analysis. For staged nTF missing-output
counts, the reported count is conditional on a record reaching the missing
stage under the model's own prior decisions. This prevents failures on records
that the model had already excluded from inflating the final-stage count.

## Agreement

- Cohen's kappa is calculated for human versus ChatGPT, human versus Gemini,
  and ChatGPT versus Gemini.
- Fleiss' kappa is calculated across the human reviewer, ChatGPT, and Gemini.
- All calculations use the exact endpoint subset defined above.

## Heterogeneity

The reported Cochran-style Q, chi-square p value, and I-squared describe
between-review heterogeneity in final nTF sensitivity and specificity. With
three reviews, the chi-square survival function has two degrees of freedom and
equals `exp(-Q/2)`.

