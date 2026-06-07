import json

# Load the original messy JSON
with open("skills_database.json", "r") as f:
    data = json.load(f)

# Fix skill format
cleaned_data = {}
for role, skills in data.items():
    cleaned_list = []
    for item in skills:
        if isinstance(item, str):
            # Split space-separated string into individual skills
            parts = item.strip().replace(",", "").split()
            cleaned_list.extend(parts)
        elif isinstance(item, list):
            cleaned_list.extend(item)
    # Remove duplicates and sort
    cleaned_data[role] = sorted(set([s.lower() for s in cleaned_list]))

# Save the cleaned JSON
with open("skills_database_cleaned.json", "w") as f:
    json.dump(cleaned_data, f, indent=2)

print("✅ skills_database_cleaned.json created successfully!")
