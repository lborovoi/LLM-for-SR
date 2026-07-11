# Results

`published/` contains the locked publication tables generated from the public
decision matrices:

- `table1_validity.csv`: confusion matrices, validity measures, Cohen's kappa,
  and missing-output counts;
- `table2_agreement.csv`: pairwise Cohen's kappa and three-rater Fleiss' kappa;
- `heterogeneity.csv`: between-review heterogeneity in final nTF sensitivity
  and specificity.

`reproduced/` is ignored by Git. Recreate it with:

```bash
python -m llm_sr_benchmark reproduce \
  --data data/locked \
  --output results/reproduced
```

