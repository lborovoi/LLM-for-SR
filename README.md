# LLM-for-SR

[![Reproduce locked results](https://github.com/lborovoi/LLM-for-SR/actions/workflows/reproduce.yml/badge.svg)](https://github.com/lborovoi/LLM-for-SR/actions/workflows/reproduce.yml)

Reproducibility companion for the manuscript **“Validity and consistency of
different LLMs in conducting public health systematic reviews: a cautious call
for hybrid approaches.”**

This repository contains the locked binary decisions, historical prompts, and
dependency-free analysis code needed to reproduce the reported validity,
agreement, and between-review heterogeneity results for three systematic
reviews. Reproduction is offline: it does not call an LLM API and does not
require an API key.

## Main finding

Providing more article text did not produce a monotonic increase in agreement.
For SR1, Cohen's kappa decreased from title screening to the human-gated
full-text endpoint:

| SR1 endpoint | N | ChatGPT kappa | Gemini kappa |
|---|---:|---:|---:|
| Title | 1,556 | 0.492 | 0.282 |
| Title/abstract | 496 | 0.259 | 0.364 |
| Full text | 86 | 0.161 | 0.273 |

The low ChatGPT full-text kappa is exactly reproducible from `27 TP / 43 FP /
1 FN / 15 TN`. Sensitivity was 96.4%, but specificity was 25.9%; the 43 false
positive inclusions reduced observed agreement to 48.8%. Because the later
stages use nested, prevalence-enriched subsets, kappa values across stages are
not a monotonic learning curve. See
[`docs/why_kappa_can_decrease.md`](docs/why_kappa_can_decrease.md) for the full
interpretation.

## Locked study flow

| Review | Starting records | Human intermediate gate(s) | Human final includes |
|---|---:|---:|---:|
| SR1: vaccination | 1,556 | 496 title; 86 title/abstract | 28 |
| SR2: post-COVID | 3,720 | No separate human title/abstract label | 74 |
| SR3: atopy | 746 | 101 title/abstract | 60 |

`TF` denotes traditional, human-gated stage evaluation. `nTF` denotes the
non-traditional end-to-end workflow in which a record must pass each model
stage. The exact endpoint and missing-output rules are locked in
[`docs/analysis_contract.md`](docs/analysis_contract.md).

## Quick reproduction

Python 3.10 or newer is sufficient; the analysis package has no runtime
dependencies.

```bash
git clone https://github.com/lborovoi/LLM-for-SR.git
cd LLM-for-SR
python -m pip install --no-deps -e .
python -m llm_sr_benchmark validate --data data/locked
python -m llm_sr_benchmark reproduce \
  --data data/locked \
  --output results/reproduced
python -m unittest discover -s tests -v
python scripts/check_public_release.py
```

The recalculated tables should match `results/published/` within floating-point
tolerance. Continuous integration runs the same checks on every commit.

## Repository contents

```text
data/locked/          pseudonymized row-level human and model decisions
data/codebook.csv     definitions for every public data field
src/                  metric, agreement, heterogeneity, validation, and CLI code
results/published/    locked publication result tables
prompts/              recovered historical system prompts and review criteria
provenance/           aggregate reconciliation record, run manifest, checksums
docs/                 endpoint contract and interpretation notes
tests/                denominator, confusion-matrix, missingness, and snapshot tests
```

## Data minimization

The public matrices contain only random opaque IDs, binary decisions, and
missing-output flags. They do not contain citation titles, abstracts, authors,
journals, DOI/PMID values, URLs, filenames, source row numbers, model reasoning,
local paths, or full-text files. Record order was randomized, and no crosswalk
from public IDs to citation identities is included or retained.

This design protects the citation set of the ongoing SR3 review while still
permitting exact reproduction of every reported metric. Historical notebooks,
bibliographic exports, article PDFs, manuscript drafts, and local execution
artifacts are intentionally outside the public repository.

## Prompt and model provenance

The prompt files preserve historical semantics and are retrospectively labelled
`v1`. Whitespace and one encoding artifact were normalized, and review labels
were neutralized to SR1–SR3. Known duplicated or ambiguous eligibility wording
was not silently corrected.

Historical code records the identifiers `gpt-4o`, `gpt-4.1-mini`, and
`google/gemini-3-flash-preview`, but does not provide a complete run-level
mapping or explicit generation parameters and seeds. The frozen decisions—not
a claim of deterministic re-generation from a mutable API—are therefore the
primary reproducibility object. Details are in
[`provenance/run_manifest.csv`](provenance/run_manifest.csv).

## Authors and citation

Leah Borovoi, Kfir Bar, Sophie Lazar, Tomer Bernstine, Jumanah Essa-Hadad,
Paul Kuodi, Nathalie Rhone, and Michael Edelstein.

Use [`CITATION.cff`](CITATION.cff) to cite this software release. Add the
article DOI to the citation after journal publication.

## Licenses

Code is released under the [MIT License](LICENSE). The pseudonymized decision
matrices and derived result tables are released under
[CC BY 4.0](LICENSE-DATA.md). No rights to third-party publication text or
bibliographic database content are conveyed.


