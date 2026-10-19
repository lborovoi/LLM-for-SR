#!/usr/bin/env python3
"""Reproduce record-derived results and the separately reported manuscript tables.

No model calls, label changes, run selection, or record exclusions occur here.
Only the Python standard library is required (Python 3.10+).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTS = ("TP", "FP", "FN", "TN")
BASE_FIELDS = ["review", "model", "workflow", "human_reference", "records_evaluated", *COUNTS,
               "sensitivity_%_(95%CI)", "specificity_%_(95%CI)", "PPV_%_(95%CI)", "NPV_%_(95%CI)"]
FIELDS = BASE_FIELDS + ["F1", "cohen_kappa", "analysis_id", "analysis_set", "manuscript_table",
                        "data_support", "decision_column", "reference_column", "gate_column", "input_source"]
GOLDS = {
    "SR1": ["Human – title gate (496)", "Human – title/abstract gate (86)", "Human – final inclusion (28)"],
    "SR2": ["Human – final inclusion (74)"],
    "SR3": ["Human – title/abstract (101)", "Human – final inclusion (60)"],
}
TARGETS = {"SR1": (1556, [496, 86, 28]), "SR2": (3720, [74]), "SR3": (746, [101, 60])}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def binary(value, *, missing_exclude=False):
    value = str(value).strip()
    if value in ("0", "1"):
        return int(value)
    if value == "" and missing_exclude:
        return 0
    raise ValueError(f"Expected a binary decision, got {value!r}")


def validate_review(review, rows):
    n, positives = TARGETS[review]
    if len(rows) != n or len({r["no"] for r in rows}) != n or any(not r["no"] for r in rows):
        raise ValueError(f"{review}: unexpected or duplicate record IDs")
    for column, expected in zip(GOLDS[review], positives):
        if sum(binary(r[column]) for r in rows) != expected:
            raise ValueError(f"{review}: unexpected reference total for {column}")
    for row in rows:
        values = [binary(row[c]) for c in GOLDS[review]]
        if any(b > a for a, b in zip(values, values[1:])):
            raise ValueError(f"{review}/{row['no']}: reference inclusion outside the preceding human gate")


def matrix(rows, decision_column, reference_column, gate_column=""):
    counts = [0, 0, 0, 0]
    for row in rows:
        if gate_column and binary(row[gate_column]) == 0:
            if str(row[decision_column]).strip() != "":
                raise ValueError(f"Decision outside the TF cohort: {decision_column}")
            continue
        truth = binary(row[reference_column])
        pred = binary(row[decision_column], missing_exclude=True)
        counts[{(1, 1): 0, (0, 1): 1, (1, 0): 2, (0, 0): 3}[truth, pred]] += 1
    return tuple(counts)


def wilson(successes, total):
    if total == 0:
        return None
    z = 1.959963984540054
    p = successes / total
    den = 1 + z*z/total
    middle = (p + z*z/(2*total))/den
    half = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/den
    return max(0.0, middle-half), min(1.0, middle+half)


def percentage(successes, total):
    interval = wilson(successes, total)
    if interval is None:
        return ""
    lo, hi = interval
    return f"{100*successes/total:.1f} ({100*lo:.1f}–{100*hi:.1f})"


def statistics(counts):
    tp, fp, fn, tn = counts
    if any(type(x) is not int or x < 0 for x in counts) or sum(counts) == 0:
        raise ValueError("Confusion-matrix counts must be non-negative integers with positive N")
    n = sum(counts)
    fden = 2*tp+fp+fn
    pe = ((tp+fn)*(tp+fp)+(tn+fp)*(tn+fn))/(n*n)
    return {
        "records_evaluated": n, **dict(zip(COUNTS, counts)),
        "sensitivity_%_(95%CI)": percentage(tp, tp+fn),
        "specificity_%_(95%CI)": percentage(tn, tn+fp),
        "PPV_%_(95%CI)": percentage(tp, tp+fp),
        "NPV_%_(95%CI)": percentage(tn, tn+fn),
        "F1": f"{2*tp/fden:.6f}" if fden else "",
        "cohen_kappa": f"{((tp+tn)/n-pe)/(1-pe):.6f}" if pe != 1 else "",
    }


def record_specs(review):
    """Use the saved decisions on their specified human-selected cohorts."""
    golds = GOLDS[review]
    if review == "SR1":
        for suffix, gold, gate in [("title (TF)", golds[0], ""),
                                   ("title/abstract (TF)", golds[1], golds[0]),
                                   ("TF full text", golds[2], golds[1]),
                                   ("nTF final", golds[2], ""),
                                   ("one-shot", golds[2], "")]:
            for model in ["GPT old", "Gemini old"]:
                if suffix == "nTF final" and model == "Gemini old":
                    model = "Gemini reconstructed (2025 TA + 2026 full text)"
                yield model, suffix, gold, gate
    elif review == "SR2":
        for model in ["GPT old", "Gemini old"]:
            yield model, "nTF final", golds[0], ""
    else:
        for suffix, gold, gate in [("title/abstract (TF)", golds[0], ""),
                                   ("TF full text", golds[1], golds[0]),
                                   ("nTF final", golds[1], "")]:
            for model in ["GPT old", "Gemini old"]:
                yield model, suffix, gold, gate
        for model in ["GPT new (6.1 Sol)", "GPT new (4.1 mini)", "Gemini new (3.8 Flash)",
                      "Gemini new (3-flash-preview)"]:
            has_ta = model != "Gemini new (3-flash-preview)"
            if has_ta:
                yield model, "title/abstract", golds[0], ""
            yield model, "TF full text", golds[1], golds[0]
            if has_ta:
                yield model, "nTF final", golds[1], ""
            yield model, "one-shot", golds[1], ""


def record_results(root):
    output = []
    for review in ("SR1", "SR2", "SR3"):
        source = f"results/{review.lower()}_decisions.csv"
        rows = read_csv(root/source)
        validate_review(review, rows)
        for model, workflow, gold, gate in record_specs(review):
            column = f"{model} – {workflow}"
            output.append({"review": review, "model": model, "workflow": workflow,
                           "human_reference": gold, **statistics(matrix(rows, column, gold, gate)),
                           "analysis_id": "", "analysis_set": "", "manuscript_table": "",
                           "data_support": "record_level", "decision_column": column,
                           "reference_column": gold, "gate_column": gate, "input_source": source})
    return output


def historical_results(root):
    source = "results/reference/sr1_historical_reported.csv"
    output = []
    for row in read_csv(root/source):
        counts = tuple(int(row[k]) for k in COUNTS)
        if sum(counts) != int(row["records_evaluated"]):
            raise ValueError("Historical aggregate denominator mismatch")
        if row["data_support"] != "reported_aggregate":
            raise ValueError("Historical summary counts must retain their aggregate-only provenance")
        output.append({"review": "SR1", "model": row["model"], "workflow": row["workflow"],
                       "human_reference": row["human_reference"], **statistics(counts),
                       "analysis_id": "", "analysis_set": "sr1_historical_reported",
                       "manuscript_table": "Table 1", "data_support": "reported_aggregate",
                       "decision_column": "", "reference_column": "", "gate_column": "",
                       "input_source": source})
    if len(output) != 8:
        raise ValueError("Expected the eight historical SR1 manuscript rows")
    return output


def csv_bytes(rows, fields=FIELDS):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def paired_specs():
    for review, workflow, gold, gate in [
        ("SR1", "title (TF)", GOLDS["SR1"][0], ""),
        ("SR1", "title/abstract (TF)", GOLDS["SR1"][1], GOLDS["SR1"][0]),
        ("SR1", "TF full text", GOLDS["SR1"][2], GOLDS["SR1"][1]),
        ("SR1", "nTF final", GOLDS["SR1"][2], ""),
        ("SR1", "one-shot", GOLDS["SR1"][2], ""),
        ("SR2", "nTF final", GOLDS["SR2"][0], ""),
        ("SR3", "title/abstract (TF)", GOLDS["SR3"][0], ""),
        ("SR3", "TF full text", GOLDS["SR3"][1], GOLDS["SR3"][0]),
        ("SR3", "nTF final", GOLDS["SR3"][1], ""),
    ]:
        model_b = "Gemini reconstructed (2025 TA + 2026 full text)" if review == "SR1" and workflow == "nTF final" else "Gemini old"
        yield review, workflow, gold, gate, "GPT old", model_b, "sr1_additional" if review == "SR1" else "historical_updated"
    for workflow, gold, gate in [("title/abstract", GOLDS["SR3"][0], ""),
                                  ("TF full text", GOLDS["SR3"][1], GOLDS["SR3"][0]),
                                  ("nTF final", GOLDS["SR3"][1], ""),
                                  ("one-shot", GOLDS["SR3"][1], "")]:
        yield "SR3", workflow, gold, gate, "GPT new (6.1 Sol)", "Gemini new (3.8 Flash)", "sr3_2026"


def combine(truth, a, b, rule):
    return {"model_A": a, "model_B": b, "OR": a | b, "AND": a & b,
            "discordant_review": truth if a != b else a}[rule]


def hybrid_results(root):
    output = []
    for pair_i, (review, workflow, gold, gate, model_a, model_b, analysis_set) in enumerate(paired_specs(), 1):
        source = f"results/{review.lower()}_decisions.csv"
        rows = read_csv(root/source)
        ca, cb = f"{model_a} – {workflow}", f"{model_b} – {workflow}"
        values = [(binary(r[gold]), binary(r[ca], missing_exclude=True), binary(r[cb], missing_exclude=True))
                  for r in rows if not gate or binary(r[gate])]
        discordant = sum(a != b for _, a, b in values)
        concordant_includes = sum(a == b == 1 for _, a, b in values)
        missed = sum(y == 1 and a == b == 0 for y, a, b in values)
        for rule in ["model_A", "model_B", "OR", "AND", "discordant_review"]:
            synthetic_pairs = [{"gold": str(y), "pred": str(combine(y, a, b, rule))} for y, a, b in values]
            stats = statistics(matrix(synthetic_pairs, "pred", "gold"))
            retained = stats["TP"]+stats["FP"]
            output.append({"analysis_id": f"table4_{pair_i:02d}_{rule}", "review": review,
                           "analysis_set": analysis_set, "workflow": workflow, "rule": rule,
                           "model_A": model_a, "model_B": model_b,
                           "human_positive": sum(y for y, _, _ in values), **stats,
                           "records_read": discordant if rule == "discordant_review" else retained,
                           "records_read_with_concordant_includes": discordant+concordant_includes if rule == "discordant_review" else retained,
                           "missed_by_both": missed, "data_support": "record_level_simulation",
                           "input_source": source})
    return output


def agreement_results(root):
    """Recompute target-N kappas; preserve separately reported paired-subset kappas."""
    reported = read_csv(root/"results/reference/table2_reported_paired_agreement.csv")
    pairs = list(paired_specs())[:9]
    if len(reported) != len(pairs):
        raise ValueError("Unexpected number of reported agreement rows")
    output = []
    for i, (meta, spec) in enumerate(zip(reported, pairs), 1):
        review, workflow, gold, gate, ma, mb, analysis_set = spec
        rows = read_csv(root/f"results/{review.lower()}_decisions.csv")
        sa = statistics(matrix(rows, f"{ma} – {workflow}", gold, gate))
        sb = statistics(matrix(rows, f"{mb} – {workflow}", gold, gate))
        n, paired_n = sa["records_evaluated"], int(meta["paired_n"])
        if meta["review"] != review or int(meta["target_N"]) != n or not 0 < paired_n <= n:
            raise ValueError("Reported paired agreement does not match its target cohort")
        for key in ["inter_model_cohen_kappa", "fleiss_kappa"]:
            if not -1 <= float(meta[key]) <= 1:
                raise ValueError("Invalid reported kappa")
        output.append({"analysis_id": f"table2_{i:02d}", "review": review, "analysis_set": analysis_set,
                       "workflow": workflow, "target_N": n,
                       "human_chatgpt_cohen_kappa": sa["cohen_kappa"],
                       "human_gemini_cohen_kappa": sb["cohen_kappa"],
                       "human_model_support": "record_level_target_N",
                       "paired_n": paired_n, "inter_model_cohen_kappa": meta["inter_model_cohen_kappa"],
                       "fleiss_kappa": meta["fleiss_kappa"], "paired_support": "reported_common_observed_subset",
                       "paired_source": meta["source"]})
    return output


def build_outputs(root=ROOT):
    record = record_results(root)
    historical = historical_results(root)
    table1 = historical + [dict(r) for r in record if
                          (r["review"] == "SR1" and r["workflow"] == "one-shot") or
                          r["review"] == "SR2" or
                          (r["review"] == "SR3" and r["model"].endswith(" old"))]
    table3 = [dict(r) for r in record if r["review"] == "SR3" and " new " in r["model"]]
    table5 = [dict(r) for r in record if r["review"] == "SR1"]
    for number, rows in [(1, table1), (3, table3), (5, table5)]:
        for i, row in enumerate(rows, 1):
            row["analysis_id"] = f"table{number}_{i:02d}"
            row["manuscript_table"] = f"Table {number}"
            if row["data_support"] == "record_level":
                row["analysis_set"] = ("sr1_additional" if row["review"] == "SR1" else
                                       "sr3_2026" if number == 3 else f"{row['review'].lower()}_updated")
            row["model"] = {"GPT old": "ChatGPT", "Gemini old": "Gemini",
                            "GPT new (6.1 Sol)": "GPT-6.1 Sol", "GPT new (4.1 mini)": "GPT-4.1 mini",
                            "Gemini new (3.8 Flash)": "Gemini 3.8 Flash",
                            "Gemini new (3-flash-preview)": "gemini-3-flash-preview"}.get(row["model"], row["model"])
    outputs = {
        "results/record_level_summary.csv": csv_bytes(record, BASE_FIELDS + ["F1", "cohen_kappa"]),
        "results/manuscript/table1_validity.csv": csv_bytes(table1),
        "results/manuscript/table3_modern_sr3.csv": csv_bytes(table3),
        "results/manuscript/table5_additional_sr1.csv": csv_bytes(table5),
        "results/summary_all_models.csv": csv_bytes(table1 + table3 + table5),
    }
    table2, table4 = agreement_results(root), hybrid_results(root)
    outputs["results/manuscript/table2_agreement.csv"] = csv_bytes(table2, list(table2[0]))
    outputs["results/manuscript/table4_hybrid_rules.csv"] = csv_bytes(table4, list(table4[0]))
    sources = json.loads((root/"provenance/analysis_sources.json").read_text())
    by_key = {(r["model"], r["workflow"]): r for r in historical}
    initial = by_key["ChatGPT", "initial screening (TF)"]
    abstract = by_key["ChatGPT", "abstract (TF)"]
    full = by_key["ChatGPT", "TF full text"]
    ntf = by_key["ChatGPT", "nTF final"]
    one = next(r for r in table1 if r["review"] == "SR1" and r["model"] == "ChatGPT" and r["workflow"] == "one-shot")
    flow = []
    for panel, stage, input_n, evaluation_n, retained, support, source in [
        ("TF", "initial screening", initial["records_evaluated"], initial["records_evaluated"], initial["TP"]+initial["FP"], "reported_aggregate", "Table 1, SR1 initial screen"),
        ("TF", "abstract", abstract["records_evaluated"], abstract["records_evaluated"], abstract["TP"]+abstract["FP"], "reported_aggregate", "Table 1, SR1 abstract"),
        ("TF", "full text", full["records_evaluated"], full["records_evaluated"], full["TP"]+full["FP"], "reported_aggregate", "Table 1, SR1 full text"),
        ("nTF", "initial screening", initial["records_evaluated"], "", initial["TP"]+initial["FP"], "reported_aggregate", "Figure 2 historical cascade"),
        ("nTF", "abstract", initial["TP"]+initial["FP"], "", sources["figure2"]["historical_cascade_after_abstract"], "reported_aggregate", "Figure 2 historical cascade"),
        ("nTF", "full text", sources["figure2"]["historical_cascade_after_abstract"], ntf["records_evaluated"], ntf["TP"]+ntf["FP"], "reported_aggregate", "Table 1 and Figure 2 historical cascade"),
        ("one-shot", "full text", sources["figure2"]["one_shot_pdfs_supplied"], one["records_evaluated"], one["TP"]+one["FP"], "record_level_result", "SR1 one-shot decisions; PDF supply count from Figure 2"),
    ]:
        flow.append(dict(review="SR1", model="ChatGPT", panel=panel, stage=stage, input_records=input_n,
                         evaluation_records=evaluation_n, model_inclusions=retained, data_support=support, source=source))
    outputs["results/manuscript/figure2_counts.csv"] = csv_bytes(flow, list(flow[0]))
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check committed outputs without writing files")
    args = parser.parse_args()
    failed = []
    for relative, content in build_outputs().items():
        path = ROOT/relative
        if args.check:
            if not path.exists() or path.read_bytes() != content:
                failed.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if failed:
        raise SystemExit("Outputs differ: " + ", ".join(failed))
    print("Verified 32 record-derived matrices, 42 validity rows, 13 hybrid comparisons and agreement provenance." if args.check
          else "Wrote record-derived results, Tables 1–5 and Figure 2 counts.")


if __name__ == "__main__":
    main()
