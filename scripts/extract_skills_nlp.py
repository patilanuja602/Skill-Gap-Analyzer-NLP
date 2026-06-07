import spacy
import re
from rapidfuzz import fuzz

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

def normalize_skill(skill):
    return re.sub(r"[^a-zA-Z0-9]+", " ", skill.lower()).strip()

def extract_skills_with_nlp(resume_text, skills_list):
    """
    Extract skills from resume text.
    Returns a dictionary: skill -> context sentence
    """
    doc = nlp(resume_text.lower())
    extracted_skills = dict()

    # Normalize expected skills
    normalized_skills = [normalize_skill(skill) for skill in skills_list]

    # Extract text chunks from resume
    all_chunks = {normalize_skill(chunk.text) for chunk in doc.noun_chunks}
    all_tokens = {normalize_skill(token.text) for token in doc if not token.is_punct}
    all_resume_parts = list(all_chunks | all_tokens)

    for expected_skill in normalized_skills:
        # Skip very short skills (1 char)
        if len(expected_skill) < 2:
            continue

        for part in all_resume_parts:
            # Whole word/phrase match with regex
            pattern = r'\b' + re.escape(expected_skill) + r'\b'
            if re.search(pattern, part):
                extracted_skills[expected_skill] = part
                break
            # Fuzzy matching for multi-word skills
            elif len(expected_skill.split()) > 1 and fuzz.partial_ratio(expected_skill, part) >= 85:
                extracted_skills[expected_skill] = part
                break

    return extracted_skills

print("✅ Skills extraction updated: now avoids false positives like 'git' in 'digit'")
