"""
app.py
Flask Web backend for TalentScout Resume Analyzer.
"""
import os
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

from pdf_parser import parse_resume
from analyzer import analyze_candidates
from pdf_export import export_candidates_to_pdf
from exceptions import TalentScoutError

app = Flask(__name__)

# Use temp directories so uploads/outputs work on Vercel's read-only
# filesystem (only /tmp is writable). Falls back to project folders locally.
def _writable_dir(name: str) -> str:
    try:
        base = os.path.join(tempfile.gettempdir(), "talentscout")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, name)
    except OSError:
        return os.path.join(os.path.dirname(__file__), name)

app.config["UPLOAD_FOLDER"] = _writable_dir("uploads")
app.config["OUTPUT_FOLDER"] = _writable_dir("outputs")

try:
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)
except OSError:
    pass  # serverless read-only filesystem; temp paths are used instead

# In-memory session candidate storage
candidates_store = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/upload", methods=["POST"])
def upload_resumes():
    global candidates_store
    if "files" not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    files = request.files.getlist("files")
    added = 0
    errors = []

    for file in files:
        if file.filename == "":
            continue
        if not file.filename.lower().endswith(".pdf"):
            errors.append(f"{file.filename}: Not a PDF file")
            continue

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        try:
            candidate = parse_resume(file_path)

            # Prevent duplicates by checking if candidate already exists by email
            candidate_email = getattr(candidate, 'email', None)
            existing_emails = [
                c.email for c in candidates_store if getattr(c, 'email', None)
            ]

            if candidate_email and candidate_email in existing_emails:
                # Update existing entry instead of adding duplicate
                idx = existing_emails.index(candidate_email)
                candidates_store[idx] = candidate
            else:
                candidates_store.append(candidate)
                added += 1

        except TalentScoutError as e:
            errors.append(f"{file.filename}: {str(e)}")
        except Exception as e:
            errors.append(f"{file.filename}: Failed to process PDF ({str(e)})")

    return jsonify({
        "added": added,
        "total": len(candidates_store),
        "errors": errors,
        "candidates": [c.to_dict() for c in candidates_store]
    })

@app.route("/api/analyze", methods=["POST"])
def run_analysis():
    global candidates_store
    data = request.json or {}
    role = data.get("role", "").strip()
    top_n = data.get("top_n", 5)

    if not candidates_store:
        return jsonify({"error": "No candidates loaded. Upload resumes first."}), 400

    try:
        ranked = analyze_candidates(candidates_store, role)

        # Filter top N candidates
        filtered = ranked[:top_n]
        return jsonify({
            "role": role,
            "total_candidates": len(candidates_store),
            "top_n": top_n,
            "results": [c.to_dict() for c in filtered]
        })
    except TalentScoutError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/export-pdf", methods=["POST"])
def export_pdf():
    global candidates_store
    data = request.json or {}
    role = data.get("role", "").strip()
    top_n = data.get("top_n", 5)

    if not candidates_store:
        return jsonify({"error": "No candidates loaded."}), 400

    try:
        ranked = analyze_candidates(candidates_store, role)
        safe_role = "".join(ch if ch.isalnum() else "_" for ch in role.lower()) or "role"
        pdf_filename = f"TalentScout_{safe_role}_Top{top_n}.pdf"
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], pdf_filename)

        export_candidates_to_pdf(
            output_path=output_path,
            role=role,
            ranked=ranked,
            top_n=top_n,
            total_candidates=len(candidates_store)
        )
        return send_file(output_path, as_attachment=True, download_name=pdf_filename)
    except Exception as e:
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500

@app.route("/api/clear", methods=["POST"])
def clear_candidates():
    global candidates_store
    candidates_store.clear()
    return jsonify({"message": "Cleared all candidates.", "total": 0})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
