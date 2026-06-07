import pandas as pd
import json
import os

# Paths to the CSV files in the data folder
kaggle_path = os.path.join("data", "job-skill-set.csv")
cse_path = os.path.join("data", "cse-job-skill-set.csv")
output_json_path = os.path.join("data", "skills_database.json")

# Load both datasets
kaggle_df = pd.read_csv(kaggle_path)
cse_df = pd.read_csv(cse_path)

# Normalize column names
kaggle_df = kaggle_df.rename(columns={"job_skill_set": "skills"})
cse_df = cse_df.rename(columns={"Skills": "skills", "Job Role": "job_title"})

# Combine both
combined_df = pd.concat([kaggle_df[["job_title", "skills"]], cse_df[["job_title", "skills"]]])

# Clean and map into JSON
mapping = {
    title.lower(): list({skill.strip().lower() for skills in group["skills"] for skill in str(skills).split(",")})
    for title, group in combined_df.groupby("job_title")
}

# Save to JSON file inside the data folder
with open(output_json_path, "w") as f:
    json.dump(mapping, f, indent=2)

print(f"✅ Combined skills_database.json created with {len(mapping)} job roles.")
