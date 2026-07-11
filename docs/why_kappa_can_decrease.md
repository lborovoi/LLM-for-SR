# Why agreement can decrease at later screening stages

The decreasing Cohen's kappa in SR1 is reproducible from the locked decision
matrix; it is not, by itself, evidence that the calculation is wrong.

For ChatGPT, the title-stage confusion matrix was 218 true positives, 17 false
positives, 278 false negatives, and 1,043 true negatives (`N=1,556`; kappa
`0.492`). At the human-gated full-text stage it was 27 true positives, 43 false
positives, 1 false negative, and 15 true negatives (`N=86`; kappa `0.161`). The
later-stage model was highly sensitive (27/28, 96.4%) but had low specificity
(15/58, 25.9%). Its 43 false-positive inclusions reduced observed agreement to
48.8%, which produces the low kappa.

Three points are important when interpreting this pattern:

1. The stage samples are nested and prevalence-enriched, not repeated
   measurements on an unchanged population. Kappa depends on the marginal
   prevalence and therefore need not rise as more article text is supplied.
2. More context does not guarantee a better calibrated inclusion threshold.
   The full-text prompt generated many inclusive decisions, preserving nearly
   all true inclusions while also retaining many human exclusions.
3. A title, title/abstract, and full-text kappa answer different endpoint
   questions. Directly treating them as a monotonic learning curve is not
   statistically justified.

The repository therefore reports confusion matrices, sensitivity,
specificity, predictive values, F1, and missing-output counts alongside kappa.
It also preserves the human-stage gates explicitly so that every denominator
can be audited.

