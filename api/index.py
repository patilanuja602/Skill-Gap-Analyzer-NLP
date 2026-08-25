import os
import sys
import json
import io
import re
from flask import Flask, request, render_template_string, jsonify
import PyPDF2

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.append(os.path.abspath("scripts"))

try:
    from extract_skills_nlp import extract_skills_with_nlp
except ImportError:
    from scripts.extract_skills_nlp import extract_skills_with_nlp

app = Flask(__name__)

# Load cleaned and fixed skills database
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Skill Gap Analyzer</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --card-border: #334155;
            --accent-color: #6366f1;
            --accent-hover: #4f46e5;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2rem 1rem;
        }

        .container {
            width: 100%;
            max-width: 800px;
        }

        .header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .header h1 {
            font-size: 2.25rem;
            font-weight: 700;
            background: linear-gradient(135deg, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }

        .header p {
            color: var(--text-secondary);
            font-size: 1rem;
        }

        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            margin-bottom: 2rem;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        label {
            display: block;
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        input[type="file"], select, input[type="text"], textarea {
            width: 100%;
            padding: 0.75rem 1rem;
            background-color: #0f172a;
            border: 1px solid var(--card-border);
            border-radius: 0.5rem;
            color: var(--text-primary);
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }

        input[type="file"]:focus, select:focus, input[type="text"]:focus, textarea:focus {
            border-color: var(--accent-color);
        }

        .btn-submit {
            width: 100%;
            background-color: var(--accent-color);
            color: white;
            padding: 0.85rem;
            font-size: 1rem;
            font-weight: 600;
            border: none;
            border-radius: 0.5rem;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.1s;
        }

        .btn-submit:hover {
            background-color: var(--accent-hover);
        }

        .btn-submit:active {
            transform: scale(0.99);
        }

        .results-section {
            margin-top: 1rem;
        }

        .score-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(192, 132, 252, 0.1));
            border: 1px solid var(--accent-color);
            border-radius: 0.75rem;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1.5rem;
        }

        .score-title {
            font-size: 1.1rem;
            font-weight: 600;
        }

        .score-badge {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--success-color);
        }

        .section-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .skills-grid {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
        }

        .skill-item {
            background-color: #0f172a;
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid var(--success-color);
        }

        .skill-name {
            font-weight: 600;
            color: #38bdf8;
            text-transform: capitalize;
        }

        .skill-context {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
            font-style: italic;
        }

        .missing-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
        }

        .tag-missing {
            background-color: rgba(239, 68, 68, 0.15);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 0.4rem 0.8rem;
            border-radius: 2rem;
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: capitalize;
        }

        .suggestion-box {
            padding: 1rem;
            border-radius: 0.5rem;
            font-size: 0.95rem;
        }

        .suggestion-good {
            background-color: rgba(16, 185, 129, 0.1);
            border: 1px solid var(--success-color);
            color: #6ee7b7;
        }

        .suggestion-average {
            background-color: rgba(245, 158, 11, 0.1);
            border: 1px solid var(--warning-color);
            color: #fcd34d;
        }

        .suggestion-poor {
            background-color: rgba(239, 68, 68, 0.1);
            border: 1px solid var(--danger-color);
            color: #fca5a5;
        }

        .error-msg {
            background-color: rgba(239, 68, 68, 0.2);
            color: #f87171;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 AI Skill Gap Analyzer</h1>
            <p>Upload your resume and select a job role to see how well it matches industry skills.</p>
        </div>

        <div class="card">
            {% if error %}
                <div class="error-msg">❌ {{ error }}</div>
            {% endif %}

            <form action="/" method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="resume">📄 Upload your resume (PDF or TXT)</label>
                    <input type="file" id="resume" name="resume" accept=".pdf,.txt" required>
                </div>

                <div class="form-group">
                    <label for="role">🎯 Select a job role</label>
                    <select id="role" name="role" onchange="toggleCustomInputs()">
                        <option value="">-- Select a Job Role --</option>
                        {% for role in roles %}
                            <option value="{{ role }}" {% if selected_role == role %}selected{% endif %}>{{ role }}</option>
                        {% endfor %}
                        <option value="Others" {% if selected_role == "Others" %}selected{% endif %}>Others</option>
                    </select>
                </div>

                <div id="custom-fields" style="display: {% if selected_role == 'Others' %}block{% else %}none{% endif %};">
                    <div class="form-group">
                        <label for="custom_role">📝 Enter your custom job title</label>
                        <input type="text" id="custom_role" name="custom_role" value="{{ custom_role }}">
                    </div>
                    <div class="form-group">
                        <label for="custom_skills">🛠️ Enter required skills (comma separated)</label>
                        <textarea id="custom_skills" name="custom_skills" rows="3">{{ custom_skills }}</textarea>
                    </div>
                </div>

                <button type="submit" class="btn-submit">🚀 Analyze Resume</button>
            </form>
        </div>

        {% if score is not none %}
        <div class="card results-section">
            <div class="score-card">
                <span class="score-title">📊 Match Score for {{ role_used }}</span>
                <span class="score-badge">✅ {{ score }}%</span>
            </div>

            <div class="section-title">✅ Skills Found in Resume</div>
            <div class="skills-grid">
                {% if found_skills %}
                    {% for skill, context in found_skills.items() %}
                        <div class="skill-item">
                            <div class="skill-name">{{ skill }}</div>
                            <div class="skill-context">"{{ context }}"</div>
                        </div>
                    {% endfor %}
                {% else %}
                    <p style="color: var(--text-secondary);">❌ No expected skills found.</p>
                {% endif %}
            </div>

            <div class="section-title">⚠️ Skills Missing from Resume</div>
            <div class="missing-tags">
                {% if missing_skills %}
                    {% for skill in missing_skills %}
                        <span class="tag-missing">{{ skill }}</span>
                    {% endfor %}
                {% else %}
                    <p style="color: var(--success-color);">✅ None — great match!</p>
                {% endif %}
            </div>

            <div class="section-title">📌 Suggestions for Improvement</div>
            {% if score >= 80 %}
                <div class="suggestion-box suggestion-good">
                    🎉 Excellent! Your resume is well-aligned with this role.
                </div>
            {% elif score >= 50 %}
                <div class="suggestion-box suggestion-average">
                    👍 You're doing good. Try adding some more skills to improve.
                </div>
            {% else %}
                <div class="suggestion-box suggestion-poor">
                    ⚠️ Consider updating your resume with more relevant skills.
                </div>
            {% endif %}
        </div>
        {% endif %}
    </div>

    <script>
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

        if not file or file.filename == "":
            return render_template_string(HTML_TEMPLATE, roles=JOB_ROLES, error="Please upload a resume file.", score=None, selected_role=selected_role)

        if custom_role:
            role_to_use = custom_role
            expected_skills = [s.strip() for s in custom_skills.split(",") if s.strip()]
        else:
            role_to_use = selected_role
            expected_skills = SKILLS_DB.get(role_to_use, [])

        if not role_to_use or not expected_skills:
            return render_template_string(HTML_TEMPLATE, roles=JOB_ROLES, error="Please select a valid job role or enter custom skills.", score=None, selected_role=selected_role)

        try:
            resume_text = extract_text_from_file(file, file.filename)
            resume_skills_dict = extract_skills_with_nlp(resume_text, expected_skills)
            score, found_skills, missing_skills = compare_skills(resume_skills_dict, expected_skills)

            return render_template_string(
                HTML_TEMPLATE,
                roles=JOB_ROLES,
                error=None,
                score=score,
                found_skills=found_skills,
                missing_skills=missing_skills,
                selected_role=selected_role,
                custom_role=custom_role,
                custom_skills=custom_skills,
                role_used=role_to_use
            )
        except Exception as e:
            return render_template_string(HTML_TEMPLATE, roles=JOB_ROLES, error=f"Error analyzing resume: {str(e)}", score=None, selected_role=selected_role)

    return render_template_string(HTML_TEMPLATE, roles=JOB_ROLES, error=None, score=None, selected_role="")

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    try:
        file = request.files.get("resume")
        role = request.form.get("role", "")
        if not file or not role:
            return jsonify({"error": "Missing file or role"}), 400
        
        expected_skills = SKILLS_DB.get(role, [])
        resume_text = extract_text_from_file(file, file.filename)
        resume_skills_dict = extract_skills_with_nlp(resume_text, expected_skills)
        score, found_skills, missing_skills = compare_skills(resume_skills_dict, expected_skills)

        return jsonify({
            "score": score,
            "found_skills": found_skills,
            "missing_skills": missing_skills,
            "role": role
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Export app for Vercel
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
