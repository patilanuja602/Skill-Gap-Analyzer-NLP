# scripts/evaluate_model.py
import json
import os
import sys
from collections import defaultdict

import pandas as pd

# allow import from scripts (so this file can be run from project root)
sys.path.append(os.path.abspath("scripts"))
try:
    from extract_skills_nlp import extract_skills_with_nlp
except Exception as e:
    raise RuntimeError("Could not import extract_skills_with_nlp from scripts/. "
                       "Run this from project root and ensure scripts/extract_skills_nlp.py exists.") from e


def normalize_skill(skill: str) -> str:
    """Normalize skill string the same way project does (lower, strip, remove extra chars)."""
    if not skill:
        return ""
    # keep only alnum and spaces, lower-case, strip
    import re
    return re.sub(r"[^a-zA-Z0-9]+", " ", skill.lower()).strip()


def evaluate_model(ground_truth_path="ground_truth.json",
                   out_per_resume_csv="results_per_resume.csv",
                   out_skill_summary_csv="skill_confusion_summary.csv"):
    # load ground truth
    with open(ground_truth_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    rows = []
    skill_stats = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0, "support": 0})

    # global counters for micro metrics
    global_TP = 0
    global_FP = 0
    global_FN = 0

    for item in dataset:
        resume_id = item.get("resume_id", "NA")
        job_role = item.get("job_role", "")
        expected_raw = item.get("expected_skills", [])
        resume_text = item.get("resume_text", "")

        expected = [normalize_skill(s) for s in expected_raw if s and s.strip()]
        # mark support (how many examples this skill should appear in)
        for sk in expected:
            skill_stats[sk]["support"] += 1

        # run your extractor (it returns dict skill -> context sentence)
        extracted_dict = extract_skills_with_nlp(resume_text, expected_raw)
        extracted_raw = list(extracted_dict.keys()) if isinstance(extracted_dict, dict) else list(extracted_dict)
        extracted = [normalize_skill(s) for s in extracted_raw if s and s.strip()]

        set_expected = set(expected)
        set_extracted = set(extracted)

        TP_skills = set_expected & set_extracted
        FP_skills = set_extracted - set_expected
        FN_skills = set_expected - set_extracted

        TP = len(TP_skills)
        FP = len(FP_skills)
        FN = len(FN_skills)

        # update global counters
        global_TP += TP
        global_FP += FP
        global_FN += FN

        # update per-skill stats
        for sk in TP_skills:
            skill_stats[sk]["TP"] += 1
        for sk in FP_skills:
            skill_stats[sk]["FP"] += 1
        for sk in FN_skills:
            skill_stats[sk]["FN"] += 1

        # metrics per resume
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        accuracy = (TP / len(expected)) if len(expected) > 0 else 0.0  # coverage of expected

        rows.append({
            "resume_id": resume_id,
            "job_role": job_role,
            "expected_skills": ";".join(expected),
            "extracted_skills": ";".join(extracted),
            "TP": TP,
            "FP": FP,
            "FN": FN,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "accuracy_pct": round(accuracy * 100, 2)
        })

    # create per-resume CSV
    df = pd.DataFrame(rows)
    df.to_csv(out_per_resume_csv, index=False, encoding="utf-8")
    print(f"Saved per-resume results → {out_per_resume_csv}")

    # per-skill confusion summary
    skill_rows = []
    for skill, stats in sorted(skill_stats.items(), key=lambda x: (-x[1]["support"], x[0])):
        TP = stats["TP"]
        FP = stats["FP"]
        FN = stats["FN"]
        support = stats["support"]
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
        skill_rows.append({
            "skill": skill,
            "TP": TP,
            "FP": FP,
            "FN": FN,
            "support": support,
            "precision": round(precision, 4),
            "recall": round(recall, 4)
        })

    df_skills = pd.DataFrame(skill_rows)
    df_skills.to_csv(out_skill_summary_csv, index=False, encoding="utf-8")
    print(f"Saved skill-level summary → {out_skill_summary_csv}")

    # global micro metrics
    micro_precision = global_TP / (global_TP + global_FP) if (global_TP + global_FP) > 0 else 0.0
    micro_recall = global_TP / (global_TP + global_FN) if (global_TP + global_FN) > 0 else 0.0
    micro_f1 = (2 * micro_precision * micro_recall / (micro_precision + micro_recall)) if (micro_precision + micro_recall) > 0 else 0.0

    # macro metrics: average of per-resume metrics
    macro_precision = df["precision"].mean() if not df["precision"].empty else 0.0
    macro_recall = df["recall"].mean() if not df["recall"].empty else 0.0
    macro_f1 = df["f1_score"].mean() if not df["f1_score"].empty else 0.0

    summary = {
        "num_resumes": len(rows),
        "global_TP": int(global_TP),
        "global_FP": int(global_FP),
        "global_FN": int(global_FN),
        "micro_precision": round(micro_precision, 4),
        "micro_recall": round(micro_recall, 4),
        "micro_f1": round(micro_f1, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4)
    }

    print("\n=== Aggregated Summary ===")
    for k, v in summary.items():
        print(f"{k}: {v}")

    # also save summary to CSV/JSON for records
    pd.DataFrame([summary]).to_csv("evaluation_summary.csv", index=False)
    with open("evaluation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("Saved aggregated summary → evaluation_summary.csv and evaluation_summary.json")
    return summary


if __name__ == "__main__":
    evaluate_model("ground_truth.json")
