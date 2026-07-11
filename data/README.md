# Public locked decision data

The three CSV files in `locked/` contain the minimum row-level information
needed to reproduce the paper's validity and agreement analyses. They contain
only opaque random record IDs, binary human/model decisions, and explicit
missing-output flags.

They deliberately do **not** contain titles, abstracts, authors, journal
names, DOI/PMID values, URLs, filenames, local paths, model reasoning, source
row numbers, or full-text files. Record order was randomized and there is no
public or retained crosswalk from the opaque IDs to citation identities.

## Coding

- `1` = include, or missing output where the flag is a missingness field.
- `0` = exclude, or observed output where the flag is a missingness field.
- Missing model outputs are represented as decision `0` in the primary
  analysis and are also marked by a corresponding `*_missing` field.
- End-to-end nTF decisions are derived in code from the stage decisions; they
  are not duplicated in the CSV files.

See `codebook.csv` for field definitions and `docs/analysis_contract.md` for
the gate and endpoint rules.

## Locked denominators

| Review | Starting records | Human intermediate gate(s) | Human final includes |
|---|---:|---:|---:|
| SR1 | 1,556 | 496 title; 86 title/abstract | 28 |
| SR2 | 3,720 | Not available as a separate human label | 74 |
| SR3 | 746 | 101 title/abstract | 60 |

The SR3 citation-level source set belongs to an ongoing review. Its public
matrix is therefore intentionally unlinkable to citation identities while
remaining sufficient for exact metric reproduction.

