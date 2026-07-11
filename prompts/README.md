# Historical screening prompts

These files preserve the prompt semantics used in the evaluated screening
workflows. The prompt bodies were recovered from the archived implementation
and manuscript appendix and retrospectively labelled `v1`; a formal prompt
version log did not exist at the time of the runs.

For publication safety and consistency, personal review labels were replaced
with `SR1`, `SR2`, and `SR3`. Whitespace and one character-encoding artifact
were normalized. Eligibility semantics were not edited. In particular, the
duplicated and potentially ambiguous wording in the SR1 criteria is retained
because correcting it after the runs would not reproduce the evaluated
condition.

The same system prompts and study criteria were used for traditional-flow
(TF) and non-traditional-flow (nTF) analyses. The workflows differed in which
records advanced to later stages, not in a newly optimized prompt.

Historical project files contain several model identifiers, but they do not
provide a complete run-level mapping or explicit generation parameters and
seeds. See `provenance/run_manifest.csv` for the resulting limitation.

## Input assembly

- Title-only screening used `system_prompt_v1.md` and supplied `<Missing>` as
  the abstract.
- Title/abstract screening used the same system prompt and supplied the
  available title, authors, year, and abstract.
- Study-specific criteria were appended after all article blocks.
- Full-text screening used `full_text_pdf_system_prompt_v1.md` with PDFs.

## Known historical discrepancy

The recovered SR1 prompt says articles were published "since 2010," whereas
the manuscript Methods describes a 2010–2021 period. This may reflect the
search-date boundary rather than a distinct prompt rule. The repository
preserves the prompt as used and does not claim that these formulations are
identical.

