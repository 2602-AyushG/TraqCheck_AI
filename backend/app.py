from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import uuid
from db import get_db, init_db
from parser import extract_text, parse_resume


load_dotenv()

app = Flask(__name__)
CORS(app)  # allow frontend requests

# Maximum upload size: 10 MB
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(__file__),
    "uploads"
)

DOCUMENTS_FOLDER = os.path.join(
    os.path.dirname(__file__),
    "documents"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOCUMENTS_FOLDER, exist_ok=True)

# Putting paths into Flask config
# This means instead of writing the folder path everywhere later,
# our routes can simply use:
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["DOCUMENTS_FOLDER"] = DOCUMENTS_FOLDER

init_db()


@app.route("/")
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Candidate AI System backend running"
    })


# step - 9

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@app.route("/candidates/upload", methods=["POST"])
def upload_candidate():

    if "resume" not in request.files:
        return jsonify({
            "error": "No file part 'resume' in request"
        }), 400

    file = request.files["resume"]

    if file.filename == "":
        return jsonify({
            "error": "No file selected"
        }), 400

    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            "error": "Only PDF and DOCX files are allowed"
        }), 400

    # Unique filename to avoid overwrites/collisions
    unique_name = f"{uuid.uuid4().hex}{ext}"

    save_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        unique_name
    )

    file.save(save_path)

    # Extract + parse
    try:
        text = extract_text(save_path)

        # Do not send empty resume text to the LLM
        if not text or not text.strip():
            parsed = {
                "error": "No readable text found in resume"
            }
        else:
            parsed = parse_resume(text)

    except Exception as e:
        return jsonify({
            "error": f"Resume processing failed: {str(e)}"
        }), 400

    # Make sure parser always returns a dictionary
    if not isinstance(parsed, dict):
        parsed = {
            "error": "AI returned invalid structured data"
        }

    if "error" in parsed:

        status = "parse_failed"

        name = None
        email = None
        phone = None
        company = None
        designation = None

        skills = []
        confidence = {}

    else:

        status = "parsed"

        name = parsed.get("name")
        email = parsed.get("email")
        phone = parsed.get("phone")
        company = parsed.get("company")
        designation = parsed.get("designation")

        skills = parsed.get("skills", [])
        confidence = parsed.get("confidence", {})

    conn = get_db()

    cursor = conn.execute(
        """INSERT INTO candidates
           (name, email, phone, company, designation, skills,
            resume_path, extraction_confidence, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            name,
            email,
            phone,
            company,
            designation,
            json.dumps(skills),
            save_path,
            json.dumps(confidence),
            status
        )
    )

    conn.commit()

    new_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "id": new_id,
        "status": status,
        "parsed_data": parsed
    }), 201


# step - 10

@app.route("/candidates", methods=["GET"])
def list_candidates():

    conn = get_db()

    rows = conn.execute(
        """SELECT id, name, email, company, designation,
                  status, created_at
           FROM candidates
           ORDER BY created_at DESC, id DESC"""
    ).fetchall()

    conn.close()

    candidates = [dict(row) for row in rows]

    return jsonify(candidates), 200


# step - 11

@app.route("/candidates/<int:candidate_id>", methods=["GET"])
def get_candidate(candidate_id):

    conn = get_db()

    row = conn.execute(
        "SELECT * FROM candidates WHERE id = ?",
        (candidate_id,)
    ).fetchone()

    conn.close()

    if row is None:
        return jsonify({
            "error": "Candidate not found"
        }), 404

    candidate = dict(row)

    # Do not expose internal server file paths through the API
    candidate.pop("resume_path", None)

    candidate["skills"] = json.loads(
        candidate["skills"] or "[]"
    )

    candidate["extraction_confidence"] = json.loads(
        candidate["extraction_confidence"] or "{}"
    )

    candidate["documents"] = json.loads(
        candidate["documents"] or "[]"
    )

    return jsonify(candidate), 200


# step - 12

from agent import generate_document_request


@app.route(
    "/candidates/<int:candidate_id>/request-documents",
    methods=["POST"]
)
def request_documents(candidate_id):

    conn = get_db()

    row = conn.execute(
        "SELECT * FROM candidates WHERE id = ?",
        (candidate_id,)
    ).fetchone()

    if row is None:
        conn.close()

        return jsonify({
            "error": "Candidate not found"
        }), 404

    candidate = dict(row)

    result = generate_document_request(candidate)

    if not result["success"]:
        conn.close()

        return jsonify({
            "error": result["error"]
        }), 400

    # If documents are already submitted,
    # do not move the status backwards.
    if candidate.get("status") == "documents_submitted":

        conn.execute(
            """UPDATE candidates
               SET document_request_text = ?
               WHERE id = ?""",
            (
                result["text"],
                candidate_id
            )
        )

        response_status = "documents_submitted"

    else:

        conn.execute(
            """UPDATE candidates
               SET document_request_text = ?, status = ?
               WHERE id = ?""",
            (
                result["text"],
                "documents_requested",
                candidate_id
            )
        )

        response_status = "documents_requested"

    conn.commit()
    conn.close()

    return jsonify({
        "id": candidate_id,
        "request_text": result["text"],
        "status": response_status
    }), 200


# step - 13

@app.route(
    "/candidates/<int:candidate_id>/submit-documents",
    methods=["POST"]
)
def submit_documents(candidate_id):

    conn = get_db()

    row = conn.execute(
        "SELECT * FROM candidates WHERE id = ?",
        (candidate_id,)
    ).fetchone()

    if row is None:
        conn.close()

        return jsonify({
            "error": "Candidate not found"
        }), 404

    if (
        "pan" not in request.files
        and "aadhaar" not in request.files
    ):
        conn.close()

        return jsonify({
            "error": (
                "No document files provided "
                "(expected 'pan' and/or 'aadhaar')"
            )
        }), 400

    saved_docs = json.loads(
        row["documents"] or "[]"
    )

    allowed_image_extensions = {
        ".png",
        ".jpg",
        ".jpeg"
    }

    for doc_type in ["pan", "aadhaar"]:

        if doc_type in request.files:

            file = request.files[doc_type]

            ext = os.path.splitext(
                file.filename
            )[1].lower()

            # Only image files are allowed
            if ext not in allowed_image_extensions:

                conn.close()

                return jsonify({
                    "error": (
                        "Only image files are allowed "
                        "for PAN and Aadhaar"
                    )
                }), 400

            # Remove previous document of the same type
            # so resubmission replaces instead of duplicating.
            saved_docs = [
                doc
                for doc in saved_docs
                if doc.get("type") != doc_type
            ]

            unique_name = (
                f"{candidate_id}_{doc_type}_"
                f"{uuid.uuid4().hex}{ext}"
            )

            save_path = os.path.join(
                app.config["DOCUMENTS_FOLDER"],
                unique_name
            )

            file.save(save_path)

            saved_docs.append({
                "type": doc_type,
                "path": save_path
            })

    # Check whether both required documents exist.
    document_types = {
        doc.get("type")
        for doc in saved_docs
    }

    if (
        "pan" in document_types
        and "aadhaar" in document_types
    ):
        status = "documents_submitted"
    else:
        status = "documents_pending"

    conn.execute(
        """UPDATE candidates
           SET documents = ?, status = ?
           WHERE id = ?""",
        (
            json.dumps(saved_docs),
            status,
            candidate_id
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "id": candidate_id,
        "documents": saved_docs,
        "status": status
    }), 200


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )