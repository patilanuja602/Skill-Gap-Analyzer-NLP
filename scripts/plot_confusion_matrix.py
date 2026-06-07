import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load the skill-level confusion summary
df = pd.read_csv("skill_confusion_summary.csv")

# Sort skills by True Positives (descending)
df_sorted = df.sort_values("TP", ascending=False)

# Reshape into confusion-matrix style (TP, FP, FN per skill)
matrix = df_sorted.set_index("skill")[["TP", "FP", "FN"]]

# Plot heatmap
plt.figure(figsize=(12, 10))
sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", cbar=False,
            annot_kws={"size": 10})  # smaller text for clarity

plt.title("Confusion Matrix per Skill", fontsize=14, pad=15)
plt.ylabel("Skills", fontsize=12)
plt.xlabel("Counts (TP = Correct, FP = Wrong, FN = Missed)", fontsize=12)

# Rotate x-axis labels for readability
plt.xticks(rotation=45, ha="right")

plt.tight_layout()

# Save image
plt.savefig("confusion_matrix_heatmap.png", dpi=300)
print("✅ Saved improved heatmap as confusion_matrix_heatmap.png")
plt.show()
