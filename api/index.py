import os
import sys
import json
import io
import re
from flask import Flask, request, render_template_string, jsonify
import PyPDF2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.append(os.path.abspath("scripts"))

try:
    from extract_skills_nlp import extract_skills_with_nlp
except ImportError:
    from scripts.extract_skills_nlp import extract_skills_with_nlp

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DB_PATH = os.path.join(BASE_DIR, "models", "skills_database_cleaned_fixed.json")

SKILLS_DB = {}
if os.path.exists(SKILLS_DB_PATH):
    with open(SKILLS_DB_PATH, "r", encoding="utf-8") as f:
        SKILLS_DB = json.load(f)

JOB_ROLES = sorted(SKILLS_DB.keys())

def extract_text_from_file(file_obj, filename):
    filename_lower = filename.lower()
    if filename_lower.endswith(".pdf"):
        reader = PyPDF2.PdfReader(io.BytesIO(file_obj.read()))
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.lower()
    else:
        return file_obj.read().decode("utf-8", errors="ignore").lower()

def compare_skills(resume_skills_dict, expected_skills):
    normalized_expected = [s.lower().strip() for s in expected_skills]
    normalized_resume = [s.lower().strip() for s in resume_skills_dict.keys()]

    found_dict = {skill: resume_skills_dict[skill] for skill in normalized_expected if skill in normalized_resume}
    missing = [skill for skill in normalized_expected if skill not in normalized_resume]

    total_expected = len(normalized_expected)
    score = round((len(found_dict) / total_expected) * 100, 2) if total_expected else 0
    return score, found_dict, missing

STREAMLIT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skill Gap Analyzer</title>
    <link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        body {
            background-color: #0e1117;
            color: #fafafa;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            padding: 2.5rem 1rem;
        }

        .streamlit-container {
            width: 100%;
            max-width: 730px;
        }

        .title-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }

        .title-emoji {
            font-size: 2.5rem;
        }

        .title-text {
            font-size: 2.5rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.02em;
        }

        .subtitle {
            color: #a3a8b4;
            font-size: 1.05rem;
            margin-bottom: 2rem;
            font-weight: 400;
        }

        .label {
            font-size: 0.9rem;
            color: #a3a8b4;
            margin-bottom: 0.5rem;
            display: block;
        }

        .uploader-box {
            background-color: #262730;
            border: 1px solid #31333f;
            border-radius: 0.5rem;
            padding: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            margin-bottom: 0.75rem;
        }

        .uploader-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .cloud-icon {
            font-size: 2rem;
            color: #808495;
        }

        .uploader-text-main {
            font-weight: 600;
            font-size: 1rem;
            color: #fafafa;
        }

        .uploader-text-sub {
            font-size: 0.8rem;
            color: #808495;
        }

        .btn-browse {
            background-color: #31333f;
            color: #fafafa;
            border: 1px solid #41444c;
            padding: 0.5rem 1rem;
            border-radius: 0.35rem;
            font-size: 0.9rem;
            cursor: pointer;
        }

        .file-chip {
            background-color: #1e2029;
            border: 1px solid #31333f;
            border-radius: 0.35rem;
            padding: 0.75rem 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            font-size: 0.9rem;
        }

        .file-chip-left {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .file-chip-name {
            color: #ffffff;
            font-weight: 600;
        }

        .file-chip-size {
            color: #808495;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        select, input[type="text"], textarea {
            width: 100%;
            background-color: #262730;
            border: 1px solid #31333f;
            border-radius: 0.5rem;
            color: #fafafa;
            padding: 0.75rem 1rem;
            font-size: 0.95rem;
            outline: none;
        }

        select:focus, input[type="text"]:focus, textarea:focus {
            border-color: #ff4b4b;
        }

        .btn-analyze {
            background-color: #262730;
            color: #fafafa;
            border: 1px solid #41444c;
            padding: 0.6rem 1.2rem;
            border-radius: 0.5rem;
            font-size: 0.95rem;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: background-color 0.15s;
            margin-bottom: 1.5rem;
        }

        .btn-analyze:hover {
            background-color: #31333f;
            border-color: #565963;
        }

        .info-box {
            background-color: #1c2a39;
            border: 1px solid #233a52;
            border-radius: 0.5rem;
            padding: 0.85rem 1.2rem;
            color: #e2f1ff;
            font-size: 0.95rem;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }

        .divider {
            height: 1px;
            background-color: #262730;
            margin: 2rem 0;
        }

        .section-header {
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }

        .score-box {
            background-color: #163824;
            border: 1px solid #215436;
            border-radius: 0.5rem;
            padding: 1rem 1.25rem;
            font-size: 1.1rem;
            font-weight: 700;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 2rem;
        }

        .skills-found-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            margin-bottom: 2rem;
        }

        .skill-found-item {
            font-size: 1.05rem;
        }

        .skill-name-bold {
            font-weight: 700;
            color: #ffffff;
        }

        .skill-arrow {
            color: #a3a8b4;
            margin: 0 0.3rem;
        }

        .skill-context-italic {
            font-style: italic;
            color: #d1d5db;
        }

        .missing-text {
            font-size: 1.05rem;
            color: #d1d5db;
            margin-bottom: 2rem;
            line-height: 1.6;
        }

        .suggestion-alert {
            background-color: #3d3714;
            border: 1px solid #574e1d;
            border-radius: 0.5rem;
            padding: 1rem 1.25rem;
            color: #ffeb99;
            font-size: 1rem;
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-top: 0.5rem;
        }

        .suggestion-good-alert {
            background-color: #163824;
            border: 1px solid #215436;
            color: #a3e635;
        }

        .hidden-file-input {
            display: none;
        }
    </style>
</head>
<body>
    <div class="streamlit-container">
        <div class="title-container">
            <span class="title-emoji">🧠</span>
            <h1 class="title-text">AI Skill Gap Analyzer</h1>
        </div>
        <p class="subtitle">Upload your resume and select a job role to see how well it matches industry skills.</p>

        <form action="/" method="POST" enctype="multipart/form-data" id="analyzer-form">
            <span class="label">Upload your resume (PDF or TXT)</span>
            
            <div class="uploader-box" onclick="document.getElementById('file-input').click()">
                <div class="uploader-left">
                    <span class="cloud-icon">☁️</span>
                    <div>
                        <div class="uploader-text-main">Drag and drop file here</div>
                        <div class="uploader-text-sub">Limit 200MB per file • PDF, TXT</div>
                    </div>
                </div>
                <button type="button" class="btn-browse">Browse files</button>
            </div>

            <input type="file" id="file-input" name="resume" class="hidden-file-input" accept=".pdf,.txt" onchange="updateFileLabel(this)">

            <div id="file-chip-container" class="file-chip" style="display: {% if filename_uploaded %}flex{% else %}none{% endif %};">
                <div class="file-chip-left">
                    <span>📄</span>
                    <span class="file-chip-name" id="chip-filename">{{ filename_uploaded or 'Uploaded_Resume.pdf' }}</span>
                </div>
                <span style="cursor: pointer; color: #808495;" onclick="clearFile()">✕</span>
            </div>

            <div class="form-group">
                <span class="label">🎯 Select a job role</span>
                <select id="role" name="role" onchange="toggleCustomInputs()">
                    <option value="">-- Select a Job Role --</option>
                    {% for role in roles %}
                        <option value="{{ role }}" {% if selected_role == role %}selected{% endif %}>{{ role }}</option>
                    {% endfor %}
                    <option value="Others" {% if selected_role == "Others" %}selected{% endif %}>Others</option>
                </select>
            </div>

            <div id="custom-fields" style="display: {% if selected_role == 'Others' %}block{% else %}none{% endif %}; margin-bottom: 1.5rem;">
                <div class="form-group">
                    <span class="label">📝 Enter your custom job title</span>
                    <input type="text" id="custom_role" name="custom_role" value="{{ custom_role }}">
                </div>
                <div class="form-group">
                    <span class="label">🛠️ Enter required skills (comma separated)</span>
                    <textarea id="custom_skills" name="custom_skills" rows="3">{{ custom_skills }}</textarea>
                </div>
            </div>

            <button type="submit" class="btn-analyze">🚀 Analyze Resume</button>
        </form>

        {% if score is not none %}
        <div class="info-box">
            ⏳ Analyzing your resume using AI-based skill matching...
        </div>

        <div class="divider"></div>

        <div class="section-header">
            📊 Match Score
        </div>
        <div class="score-box">
            ✅ {{ score }}%
        </div>

        <div class="section-header">
            ✅ Skills Found in Resume
        </div>
        <div class="skills-found-list">
            {% if found_skills %}
                {% for skill, context in found_skills.items() %}
                    <div class="skill-found-item">
                        <span class="skill-name-bold">{{ skill }}</span>
                        <span class="skill-arrow">→</span>
                        <span class="skill-context-italic">{{ context }}</span>
                    </div>
                {% endfor %}
            {% else %}
                <p style="color: #a3a8b4;">❌ No expected skills found.</p>
            {% endif %}
        </div>

        <div class="section-header">
            ⚠️ Skills Missing from Resume
        </div>
        <p class="missing-text">
            {% if missing_skills %}
                {{ missing_skills | join(', ') }}
            {% else %}
                ✅ None — great match!
            {% endif %}
        </p>

        <div class="section-header">
            📌 Suggestions for Improvement
        </div>
        {% if score >= 80 %}
            <div class="suggestion-alert suggestion-good-alert">
                🎉 Excellent! Your resume is well-aligned with this role.
            </div>
        {% elif score >= 50 %}
            <div class="suggestion-alert">
                👍 You're doing good. Try adding some more skills to improve.
            </div>
        {% else %}
            <div class="suggestion-alert">
                ⚠️ Consider updating your resume with more relevant skills.
            </div>
        {% endif %}
        {% endif %}
    </div>

    <script>
        function updateFileLabel(input) {
            var chip = document.getElementById("file-chip-container");
            var nameSpan = document.getElementById("chip-filename");
            if (input.files && input.files[0]) {
                nameSpan.innerText = input.files[0].name;
                chip.style.display = "flex";
            }
        }

        function clearFile() {
            var input = document.getElementById("file-input");
            var chip = document.getElementById("file-chip-container");
            input.value = "";
            chip.style.display = "none";
        }

        function toggleCustomInputs() {
            var roleSelect = document.getElementById("role");
            var customFields = document.getElementById("custom-fields");
            if (roleSelect.value === "Others") {
                customFields.style.display = "block";
            } else {
                customFields.style.display = "none";
            }
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("resume")
        selected_role = request.form.get("role", "")
        custom_role = request.form.get("custom_role", "").strip()
        custom_skills = request.form.get("custom_skills", "").strip()

        filename_uploaded = file.filename if file else ""

        if not file or file.filename == "":
            return render_template_string(STREAMLIT_HTML_TEMPLATE, roles=JOB_ROLES, error="Please upload a resume file.", score=None, selected_role=selected_role, filename_uploaded="")

        if custom_role:
            role_to_use = custom_role
            expected_skills = [s.strip() for s in custom_skills.split(",") if s.strip()]
        else:
            role_to_use = selected_role
            expected_skills = SKILLS_DB.get(role_to_use, [])

        if not role_to_use or not expected_skills:
            return render_template_string(STREAMLIT_HTML_TEMPLATE, roles=JOB_ROLES, error="Please select a valid job role or enter custom skills.", score=None, selected_role=selected_role, filename_uploaded=filename_uploaded)

        try:
            resume_text = extract_text_from_file(file, file.filename)
            resume_skills_dict = extract_skills_with_nlp(resume_text, expected_skills)
            score, found_skills, missing_skills = compare_skills(resume_skills_dict, expected_skills)

            return render_template_string(
                STREAMLIT_HTML_TEMPLATE,
                roles=JOB_ROLES,
                error=None,
                score=score,
                found_skills=found_skills,
                missing_skills=missing_skills,
                selected_role=selected_role,
                custom_role=custom_role,
                custom_skills=custom_skills,
                role_used=role_to_use,
                filename_uploaded=filename_uploaded
            )
        except Exception as e:
            return render_template_string(STREAMLIT_HTML_TEMPLATE, roles=JOB_ROLES, error=f"Error analyzing resume: {str(e)}", score=None, selected_role=selected_role, filename_uploaded=filename_uploaded)

    return render_template_string(STREAMLIT_HTML_TEMPLATE, roles=JOB_ROLES, error=None, score=None, selected_role="", filename_uploaded="")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
