import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


# =========================================================
# 1. Heatmap: Confusion Matrix per Skill
# =========================================================
def plot_confusion_matrix():
    df = pd.read_csv("skill_confusion_summary.csv")

    # Sort skills by TP (most detected on top)
    df_sorted = df.sort_values("TP", ascending=False)

    # Matrix (TP, FP, FN)
    matrix = df_sorted.set_index("skill")[["TP", "FP", "FN"]]

    # Replace 0s with NaN to avoid clutter in annotations
    annot_matrix = matrix.mask(matrix == 0, "")

    plt.figure(figsize=(14, 12))
    sns.heatmap(matrix, annot=annot_matrix, fmt="", cmap="Blues", cbar=True,
                linewidths=0.5, linecolor='gray')

    plt.title("Confusion Matrix per Skill", fontsize=16, pad=15)
    plt.ylabel("Skills", fontsize=12)
    plt.xlabel("Counts (TP = Correct, FP = Wrong, FN = Missed)", fontsize=12)
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig("confusion_matrix_clean.png", dpi=300)
    plt.close()
    print("✅ Saved confusion_matrix_clean.png")


# =========================================================
# 2. Bar Chart: Skill-wise TP/FP/FN
# =========================================================
def plot_skill_confusion_bar():
    df = pd.read_csv("skill_confusion_summary.csv")

    df_melted = df.melt(id_vars="skill", value_vars=["TP", "FP", "FN"],
                        var_name="Type", value_name="Count")

    plt.figure(figsize=(14, 6))
    sns.barplot(data=df_melted, x="skill", y="Count", hue="Type",
                palette={"TP": "green", "FP": "red", "FN": "orange"})

    plt.title("Skill-wise Confusion (TP/FP/FN)", fontsize=16, pad=15)
    plt.ylabel("Counts", fontsize=12)
    plt.xlabel("Skills", fontsize=12)
    plt.xticks(rotation=75, ha="right")

    plt.tight_layout()
    plt.savefig("skill_confusion_bar.png", dpi=300)
    plt.close()
    print("✅ Saved skill_confusion_bar.png")


# =========================================================
# 3. Accuracy Chart: Micro vs Macro Metrics
# =========================================================
def plot_accuracy_chart():
    df = pd.read_csv("evaluation_summary.csv")

    # Extract only the metric columns
    metrics = {
        "Precision": [df["micro_precision"].iloc[0], df["macro_precision"].iloc[0]],
        "Recall": [df["micro_recall"].iloc[0], df["macro_recall"].iloc[0]],
        "F1-Score": [df["micro_f1"].iloc[0], df["macro_f1"].iloc[0]]
    }

    df_plot = pd.DataFrame(metrics, index=["Micro", "Macro"]).reset_index()
    df_plot = df_plot.melt(id_vars="index", var_name="Metric", value_name="Score")
    df_plot.rename(columns={"index": "Type"}, inplace=True)

    plt.figure(figsize=(8, 6))
    ax = sns.barplot(data=df_plot, x="Metric", y="Score", hue="Type", palette="Set2")

    # Add values on top of bars
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.2f}",
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha="center", va="bottom", fontsize=10, color="black", xytext=(0, 3),
                    textcoords="offset points")

    plt.title("Evaluation Metrics (Micro vs Macro)", fontsize=16, pad=15)
    plt.ylabel("Score", fontsize=12)
    plt.xlabel("Metrics", fontsize=12)
    plt.ylim(0, 1)

    plt.tight_layout()
    plt.savefig("accuracy_chart.png", dpi=300)
    plt.close()
    print("✅ Saved accuracy_chart.png")


# =========================================================
# Run all three plots
# =========================================================
if __name__ == "__main__":
    plot_confusion_matrix()
    plot_skill_confusion_bar()
    plot_accuracy_chart()
