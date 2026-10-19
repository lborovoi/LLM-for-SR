import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reproduce", ROOT/"scripts/reproduce_results.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReproductionTests(unittest.TestCase):
    def test_missing_is_exclude_within_target_not_outside_gate(self):
        rows = [{"gate": "1", "gold": "1", "decision": "1"},
                {"gate": "1", "gold": "0", "decision": ""},
                {"gate": "0", "gold": "0", "decision": ""}]
        self.assertEqual(module.matrix(rows, "decision", "gold", "gate"), (1, 0, 0, 1))
        self.assertEqual(module.matrix(rows, "decision", "gold"), (1, 0, 0, 2))

    def test_nonbinary_and_decision_outside_cohort_are_errors(self):
        with self.assertRaises(ValueError):
            module.binary("MAYBE", missing_exclude=True)
        with self.assertRaises(ValueError):
            module.matrix([{"gate": "0", "gold": "0", "decision": "1"}], "decision", "gold", "gate")

    def test_statistics_independent_known_matrix(self):
        stats = module.statistics((20, 5, 10, 65))
        self.assertAlmostEqual(float(stats["F1"]), 40/55, places=6)
        self.assertEqual(float(stats["cohen_kappa"]), 0.625)
        lo, hi = module.wilson(0, 100)
        self.assertAlmostEqual(lo, 0)
        self.assertAlmostEqual(hi, 0.0369934982)

    def test_undefined_rates_are_unavailable(self):
        stats = module.statistics((0, 0, 0, 10))
        self.assertEqual(stats["sensitivity_%_(95%CI)"], "")
        self.assertEqual(stats["PPV_%_(95%CI)"], "")
        self.assertEqual(stats["cohen_kappa"], "")

    def test_historical_gemini_corpus_is_human_gated(self):
        rows = module.historical_results(ROOT)
        full = next(r for r in rows if r["model"] == "Gemini" and r["workflow"] == "TF full text")
        corpus = next(r for r in rows if r["workflow"] == "human-gated corpus estimate")
        self.assertEqual([corpus[k] for k in ["TP", "FP", "FN"]], [full[k] for k in ["TP", "FP", "FN"]])
        self.assertEqual(corpus["TN"], full["TN"]+1470)
        self.assertEqual(corpus["data_support"], "reported_aggregate")

    def test_modern_ntf_reuses_fulltext_with_own_gate(self):
        rows = module.read_csv(ROOT/"results/sr3_decisions.csv")
        for model in ["GPT new (6.1 Sol)", "GPT new (4.1 mini)", "Gemini new (3.8 Flash)"]:
            for row in rows:
                self.assertEqual(module.binary(row[f"{model} – nTF final"]),
                                 module.binary(row[f"{model} – title/abstract"])*module.binary(row[f"{model} – one-shot"]))

    def test_hybrid_reference_adjudication_cannot_recover_dual_miss(self):
        self.assertEqual(module.combine(1, 0, 1, "discordant_review"), 1)
        self.assertEqual(module.combine(0, 0, 1, "discordant_review"), 0)
        self.assertEqual(module.combine(1, 0, 0, "discordant_review"), 0)
        for row in module.hybrid_results(ROOT):
            if row["rule"] == "discordant_review":
                self.assertGreaterEqual(row["records_read_with_concordant_includes"], row["records_read"])
                self.assertEqual(row["FN"], row["missed_by_both"])

    def test_outputs_reproduce_and_raw_files_remain_unchanged(self):
        import hashlib
        import json
        manifest = json.loads((ROOT/"provenance/analysis_sources.json").read_text())
        for relative, expected in {**manifest["record_decision_sha256"], **manifest["aggregate_input_sha256"]}.items():
            self.assertEqual(hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(), expected)
        for relative, expected in module.build_outputs().items():
            self.assertEqual((ROOT/relative).read_bytes(), expected, relative)
        self.assertEqual(len(module.read_csv(ROOT/"results/summary_all_models.csv")), 42)
        self.assertEqual(len(module.read_csv(ROOT/"results/record_level_summary.csv")), 32)


if __name__ == "__main__":
    unittest.main()
