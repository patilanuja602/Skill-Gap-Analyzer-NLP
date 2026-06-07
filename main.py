import streamlit as st
import PyPDF2
import io
import json
import sys
import os

# 🔧 Allow import from scripts folder
sys.path.append(os.path.abspath("scripts"))
from extract_skills_nlp import extract_skills_with_nlp  # ✅ Now this works

# ✅ Load cleaned and fixed skills database
with open("models/skills_database_cleaned_fixed.json", "r") as f:
    SKILLS_DB = json.load(f)

job_roles = sorted(SKILLS_DB.keys())

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Skill Gap Analyzer", page_icon="🧠", layout="centered")
st.title("🧠 AI Skill Gap Analyzer")
st.markdown("Upload your resume and select a job role to see how well it matches industry skills.")

uploaded_file = st.file_uploader(" Upload your resume (PDF or TXT)", type=["pdf", "txt"])

# --- Job role selection ---
selected_role = st.selectbox("🎯 Select a job role", [""] + job_roles + ["Others"])
custom_role_input = ""
custom_skills_input = ""

if selected_role == "Others":
    custom_role_input = st.text_input("📝 Enter your custom job title")
    custom_skills_input = st.text_area("🛠️ Enter required skills (comma separated)")

analyze = st.button("🚀 Analyze Resume")

# --- Decide role and skills to use ---
if custom_role_input.strip():
    role_to_use = custom_role_input.strip()
    expected_skills = [s.strip() for s in custom_skills_input.split(",") if s.strip()]
else:
    role_to_use = selected_role
    expected_skills = SKILLS_DB.get(role_to_use, [])

# --- Resume Text Extraction ---
def extract_text(file):
    if file.type == "application/pdf":
        reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.lower()
    else:
        return file.read().decode("utf-8").lower()

# --- Skill comparison logic with context ---
def compare_skills(resume_skills_dict, expected_skills):
    """
    Returns match score, dict of found skills with context, list of missing skills
    """
    normalized_expected = [s.lower().strip() for s in expected_skills]
    normalized_resume = [s.lower().strip() for s in resume_skills_dict.keys()]

    found_dict = {skill: resume_skills_dict[skill] for skill in normalized_expected if skill in normalized_resume}
    missing = [skill for skill in normalized_expected if skill not in normalized_resume]

    total_expected = len(normalized_expected)
    score = round((len(found_dict) / total_expected) * 100, 2) if total_expected else 0

    return score, found_dict, missing

# --- Main Logic ---
if analyze:
    if not uploaded_file:
        st.error("❌ Please upload a resume file.")
    elif not role_to_use:
        st.warning("⚠️ Please select a valid job role or enter a custom role.")
    else:
        st.info("⏳ Analyzing your resume using AI-based skill matching...")
        resume_text = extract_text(uploaded_file)

        # Extract skills with context
        resume_skills_dict = extract_skills_with_nlp(resume_text, expected_skills)
        score, found_skills, missing_skills = compare_skills(resume_skills_dict, expected_skills)

        # --- Display Results ---
        st.subheader("📊 Match Score")
        st.success(f"✅ {score}%")

        st.subheader("✅ Skills Found in Resume")
        if found_skills:
            for skill, context in found_skills.items():
                st.markdown(f"**{skill}** → _{context}_")
        else:
            st.write("❌ No expected skills found.")

        st.subheader("⚠️ Skills Missing from Resume")
        st.write(", ".join(missing_skills) if missing_skills else "✅ None — great match!")

        st.subheader("📌 Suggestions for Improvement")
        if score >= 80:
            st.success("🎉 Excellent! Your resume is well-aligned with this role.")
        elif score >= 50:
            st.info("👍 You're doing good. Try adding some more skills to improve.")
        else:
            st.warning("⚠️ Consider updating your resume with more relevant skills.")