"""
Offline API tests for TraqCheck_AI. No network, no API key needed: the LLM is mocked.

Run from the backend/ folder:
    pip install pytest
    pytest test_api.py -v

Each test asserts the CORRECT behaviour. A failing test = a real bug to fix.
"""
import io
import json
import os
import tempfile
import types

import pytest

import db

# Point the DB at a temp file BEFORE importing app (app calls init_db() on import)
_TMP = tempfile.mkdtemp()
db.DB_PATH = os.path.join(_TMP, "test.db")

import app as app_module  # noqa: E402
import agent  # noqa: E402

GOOD_PARSE = {
    "name": "Riya Sharma", "email": "riya@example.com", "phone": "+91 9876543210",
    "company": "Acme Corp", "designation": "Backend Engineer",
    "skills": ["Python", "SQL"],
    "confidence": {"name": 0.99, "email": 0.99, "phone": 0.9, "company": 0.8, "designation": 0.8},
}


@pytest.fixture()
def client(monkeypatch):
    # fresh DB + upload folders per test
    db.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")
    db.init_db()
    app_module.app.config["UPLOAD_FOLDER"] = tempfile.mkdtemp()
    app_module.app.config["DOCUMENTS_FOLDER"] = tempfile.mkdtemp()
    app_module.app.config["TESTING"] = True
    monkeypatch.setattr(app_module, "extract_text", lambda p: "some resume text")
    monkeypatch.setattr(app_module, "parse_resume", lambda t: dict(GOOD_PARSE))
    monkeypatch.setattr(
        app_module, "generate_document_request",
        lambda c: {"success": True, "text": "Hi, please send PAN and Aadhaar."},
    )
    return app_module.app.test_client()


def upload(client, name="cv.pdf", content=b"%PDF-fake"):
    return client.post("/candidates/upload", data={"resume": (io.BytesIO(content), name)},
                       content_type="multipart/form-data")


def submit(client, cid, **files):
    data = {k: (io.BytesIO(b"img"), v) for k, v in files.items()}
    return client.post(f"/candidates/{cid}/submit-documents", data=data,
                       content_type="multipart/form-data")


# ---------------------------------------------------------------- basics
def test_health(client):
    assert client.get("/").status_code == 200


def test_upload_no_file_is_400(client):
    assert client.post("/candidates/upload").status_code == 400


def test_upload_wrong_extension_is_400(client):
    assert upload(client, "notes.txt").status_code == 400


def test_upload_valid_creates_candidate(client):
    r = upload(client)
    assert r.status_code == 201
    cid = r.get_json()["id"]
    got = client.get(f"/candidates/{cid}").get_json()
    assert got["name"] == "Riya Sharma" and got["skills"] == ["Python", "SQL"]


def test_get_missing_candidate_404(client):
    assert client.get("/candidates/9999").status_code == 404


def test_submit_to_missing_candidate_404(client):
    assert submit(client, 9999, pan="a.png").status_code == 404


def test_submit_with_no_files_is_400(client):
    cid = upload(client).get_json()["id"]
    assert client.post(f"/candidates/{cid}/submit-documents").status_code == 400


# ---------------------------------------------------------------- upload robustness
def test_corrupt_pdf_is_client_error_not_500(client, monkeypatch):
    monkeypatch.undo()  # use the REAL extract_text on garbage bytes
    r = upload(client, "bad.pdf", b"this is not a pdf")
    assert 400 <= r.status_code < 500


def test_empty_text_resume_not_sent_to_llm(client, monkeypatch):
    """Scanned/image PDFs give empty text. Sending '' to the LLM invites hallucination."""
    called = []
    monkeypatch.setattr(app_module, "extract_text", lambda p: "")
    monkeypatch.setattr(app_module, "parse_resume", lambda t: called.append(t) or dict(GOOD_PARSE))
    r = upload(client)
    assert not called, "empty text was sent to the LLM"
    assert r.get_json()["status"] == "parse_failed" or r.status_code >= 400


def test_llm_returning_non_dict_does_not_crash(client, monkeypatch):
    monkeypatch.setattr(app_module, "parse_resume", lambda t: [])
    assert upload(client).status_code != 500


def test_llm_exception_returns_json_error(client, monkeypatch):
    def boom(t):
        raise RuntimeError("429 rate limited")
    monkeypatch.setattr(app_module, "parse_resume", boom)
    r = upload(client)
    assert r.status_code >= 400 and r.get_json()["error"]


def test_upload_has_size_limit(client):
    assert app_module.app.config.get("MAX_CONTENT_LENGTH"), "no MAX_CONTENT_LENGTH set"


# ---------------------------------------------------------------- data exposure
def test_api_does_not_leak_server_paths(client):
    cid = upload(client).get_json()["id"]
    submit(client, cid, pan="p.png")
    body = json.dumps(client.get(f"/candidates/{cid}").get_json())
    assert "resume_path" not in body
    assert os.sep + "documents" + os.sep not in body, "absolute document path leaked"


# ---------------------------------------------------------------- request-documents
def test_request_documents_happy_path(client):
    cid = upload(client).get_json()["id"]
    r = client.post(f"/candidates/{cid}/request-documents")
    assert r.status_code == 200 and r.get_json()["status"] == "documents_requested"


def test_request_documents_works_for_fresher_without_company(client, monkeypatch):
    """Freshers/students have no company. Real agent rejects them (see agent.py)."""
    monkeypatch.setattr(app_module, "parse_resume", lambda t: {**GOOD_PARSE, "company": None})
    cid = upload(client).get_json()["id"]
    monkeypatch.undo()  # restore the REAL generate_document_request
    monkeypatch.setattr(agent.client.chat.completions, "create", _fake_llm("Hello"))
    r = client.post(f"/candidates/{cid}/request-documents")
    assert r.status_code == 200


def test_request_documents_does_not_regress_status(client):
    cid = upload(client).get_json()["id"]
    submit(client, cid, pan="p.png", aadhaar="a.png")
    client.post(f"/candidates/{cid}/request-documents")
    status = client.get(f"/candidates/{cid}").get_json()["status"]
    assert status == "documents_submitted", f"status went backwards to {status}"


def _fake_llm(text=None, choices_none=False):
    def create(**kw):
        if choices_none:
            return types.SimpleNamespace(choices=None)
        msg = types.SimpleNamespace(content=text)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])
    return create


def test_agent_handles_choices_none(monkeypatch):
    monkeypatch.setattr(agent.client.chat.completions, "create", _fake_llm(choices_none=True))
    out = agent.generate_document_request({"name": "A", "company": "B", "designation": "C"})
    assert out["success"] is False


def test_agent_handles_none_content(monkeypatch):
    monkeypatch.setattr(agent.client.chat.completions, "create", _fake_llm(text=None))
    out = agent.generate_document_request({"name": "A", "company": "B", "designation": "C"})
    assert out["success"] is False


# ---------------------------------------------------------------- submit-documents
def test_partial_submission_is_not_marked_complete(client):
    cid = upload(client).get_json()["id"]
    r = submit(client, cid, pan="p.png")
    assert r.get_json()["status"] != "documents_submitted", "only PAN uploaded but marked complete"


def test_both_documents_marks_complete(client):
    cid = upload(client).get_json()["id"]
    r = submit(client, cid, pan="p.png", aadhaar="a.png")
    assert r.get_json()["status"] == "documents_submitted"


def test_submit_rejects_non_image_files(client):
    cid = upload(client).get_json()["id"]
    assert submit(client, cid, pan="malware.exe").status_code == 400


def test_resubmitting_replaces_instead_of_duplicating(client):
    cid = upload(client).get_json()["id"]
    submit(client, cid, pan="p1.png")
    submit(client, cid, pan="p2.png")
    docs = client.get(f"/candidates/{cid}").get_json()["documents"]
    assert [d["type"] for d in docs].count("pan") == 1


# ---------------------------------------------------------------- listing
def test_list_is_newest_first(client):
    ids = [upload(client).get_json()["id"] for _ in range(3)]
    listed = [c["id"] for c in client.get("/candidates").get_json()]
    assert listed == sorted(ids, reverse=True)