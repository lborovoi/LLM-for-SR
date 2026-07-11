# Provenance and limitations

`reconciliation_decisions.csv` documents the aggregate transformations used
to produce the locked analysis without disclosing citation identities or local
project structure. `run_manifest.csv` records the model identifiers recoverable
from historical code and the limits of that record.

The repository reproduces the analysis from frozen model decisions. It does
not claim that a new API call to a mutable model name will yield the same
decision, and no API credentials are required or accepted by the analysis
package.

`checksums.sha256` covers the public decision matrices, published result tables,
prompts, and provenance tables. Run `python scripts/check_public_release.py`
to verify those files and scan the repository for common release hazards.

