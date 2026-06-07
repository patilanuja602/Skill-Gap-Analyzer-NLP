import json

# Step 1: Load messy skill database
with open('models/skills_database_cleaned.json', 'r') as f:
    raw_data = json.load(f)

# Step 2: Create a cleaned version of the skills
cleaned_data = {}

for role, skills in raw_data.items():
    clean_skills = []
    for skill in skills:
        # Fix quotes, brackets, spaces
        clean = skill.strip().replace("'", "").replace('"', '').replace("]", "").replace("[", "")
        if clean and clean.lower() not in clean_skills:
            clean_skills.append(clean.lower())
    cleaned_data[role] = sorted(set(clean_skills))

# Step 3: Save to the new fixed JSON file
with open('models/skills_database_cleaned_fixed.json', 'w') as f:
    json.dump(cleaned_data, f, indent=4)

print("✅ Skills cleaned and saved to models/skills_database_cleaned_fixed.json")
