import os
from pathlib import Path

import pytest

from parser import extract_text, parse_resume


# Set these before running the tests.
#
# Example:
# export GAURI_CV="/Users/ayushgupta/Desktop/candidate-ai-system/tnp resume gauri (1).docx"
# export TWO_COLUMN_CV="/Users/ayushgupta/Desktop/candidate-ai-system/2 col cv.pdf"
#
# Then:
# pytest test_resume_parsing.py -v


GAURI_CV = os.getenv("GAURI_CV")
TWO_COLUMN_CV = os.getenv("TWO_COLUMN_CV")


def _require_path(env_name, path_value):
    if not path_value:
        pytest.skip(
            f"{env_name} is not set. Set it to the local resume path before running."
        )

    path = Path(path_value).expanduser()

    if not path.exists():
        pytest.fail(f"{env_name} points to a file that does not exist: {path}")

    return path


def test_gauri_resume_docx_extraction():
    """
    Checks the DOCX extraction layer independently.

    This specifically verifies that contact information and table content
    are visible to the parser before the LLM is called.
    """
    path = _require_path("GAURI_CV", GAURI_CV)

    text = extract_text(str(path))

    assert text.strip(), "Gauri CV produced no extracted text"

    # These are high-confidence details visible in the supplied CV.
    assert "Gauri" in text
    assert "Vermagauri1308@gmail.com" in text
    assert "8287035447" in text
    assert "DRDO" in text
    assert "Winter Intern" in text


def test_gauri_resume_end_to_end_parsing():
    """
    Runs the actual extraction + OpenRouter parsing pipeline.

    Expected high-confidence fields:
      name        -> Gauri Verma
      email       -> Vermagauri1308@gmail.com
      phone       -> +91 8287035447
      company     -> DRDO
      designation -> Winter Intern
    """
    path = _require_path("GAURI_CV", GAURI_CV)

    text = extract_text(str(path))
    assert text.strip(), "Gauri CV produced no extracted text"

    result = parse_resume(text)

    assert isinstance(result, dict), f"Parser returned: {result}"
    assert "error" not in result, f"Parser failed: {result}"

    assert result.get("name") == "Gauri Verma"
    assert result.get("email") == "Vermagauri1308@gmail.com"

    phone = str(result.get("phone") or "").replace(" ", "").replace("-", "")
    assert "8287035447" in phone

    assert result.get("company") == "DRDO"
    assert result.get("designation") == "Winter Intern"


def test_two_column_resume_extraction():
    """
    Verifies that a two-column/scanned PDF is no longer empty.

    The new parser uses normal PDF extraction first and OCR as a fallback.
    """
    path = _require_path("TWO_COLUMN_CV", TWO_COLUMN_CV)

    text = extract_text(str(path))

    assert text.strip(), (
        "Two-column CV produced empty text. "
        "Check PyMuPDF, pytesseract, Pillow and system Tesseract."
    )

    # A useful sanity check: a real resume should contain several words,
    # not just one accidental OCR character.
    words = text.split()
    assert len(words) >= 20, (
        f"Only {len(words)} words were extracted from the two-column CV."
    )


def test_two_column_resume_end_to_end_parsing():
    """
    Runs the actual extraction + OpenRouter parsing pipeline on the
    two-column CV.

    We intentionally do NOT hard-code the candidate's exact fields here,
    because the supplied two-column resume may differ between test files.
    The important requirement is that the pipeline returns structured data
    instead of failing because PDF extraction returned empty text.
    """
    path = _require_path("TWO_COLUMN_CV", TWO_COLUMN_CV)

    text = extract_text(str(path))
    assert text.strip(), "Two-column CV produced no extracted text"

    result = parse_resume(text)

    assert isinstance(result, dict), f"Parser returned: {result}"
    assert "error" not in result, f"Two-column CV parsing failed: {result}"

    assert result.get("name"), f"Name was not extracted: {result}"
    assert result.get("skills") is not None, f"Skills missing: {result}"
