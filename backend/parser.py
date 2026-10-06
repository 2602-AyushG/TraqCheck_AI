import json
import os
import pdfplumber
import docx
import fitz
import pytesseract
from PIL import Image
import io
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()  # ELSE os library wont be able to fetch api key from .env file


def extract_text(file_path):

    if file_path.lower().endswith(".pdf"):

        text = ""

        with pdfplumber.open(file_path) as pdf:

            for page in pdf.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

        # OCR fallback for scanned/image-based PDFs
        if not text.strip():

            doc = fitz.open(file_path)

            for page in doc:

                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

                image = Image.open(
                    io.BytesIO(
                        pix.tobytes("png")
                    )
                )

                ocr_text = pytesseract.image_to_string(image)

                if ocr_text.strip():
                    text += ocr_text + "\n"

            doc.close()

        return text

    elif file_path.lower().endswith(".docx"):

        doc = docx.Document(file_path)
        text_parts = []

        # Extract normal paragraphs
        for p in doc.paragraphs:
            if p.text.strip():
                text_parts.append(p.text)

    # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        text_parts.append(cell_text)

        return "\n".join(text_parts)
        # return "\n".join(
        #     p.text
        #     for p in doc.paragraphs
        # )

    else:

        raise ValueError("Unsupported file format")


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


# actual prompt that is given to the llm
EXTRACTION_PROMPT = """Extract the following fields from this resume text.
Return ONLY valid JSON, no markdown, no explanation, in this exact shape:
{{
  "name": "...", "email": "...", "phone": "...",
  "company": "...", "designation": "...",
  "skills": ["...", "..."],
  "confidence": {{"name": 0.0-1.0, "email": 0.0-1.0, "phone": 0.0-1.0,
                  "company": 0.0-1.0, "designation": 0.0-1.0}}
}}
If a field is not found, use null and confidence 0.

Resume text:
{resume_text}
"""


# main function which calls LLM
def parse_resume(resume_text):

    # Don't send empty resume text to the LLM
    if not resume_text or not resume_text.strip():

        return {
            "error": "No readable text found in resume"
        }

    try:

        response = client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(
                        resume_text=resume_text
                    )
                }
            ],
            temperature=0,
        )

        # Handle missing/empty choices
        if not response.choices:

            return {
                "error": "AI service is temporarily unavailable"
            }

        # Handle missing message
        if response.choices[0].message is None:

            return {
                "error": "AI returned an empty response"
            }

        # Handle missing content
        if response.choices[0].message.content is None:

            return {
                "error": "AI returned an empty response"
            }

        raw = response.choices[0].message.content.strip()

        # Handle empty content
        if not raw:

            return {
                "error": "AI returned an empty response"
            }

        # Remove markdown JSON code fences
        raw = (
            raw
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        try:

            result = json.loads(raw)

            # JSON must be an object/dictionary
            if not isinstance(result, dict):

                return {
                    "error": "AI returned invalid structured data"
                }

            if isinstance(result.get("name"), str):
                result["name"] = result["name"].title()

            return result

        except json.JSONDecodeError:

            # If AI returned invalid JSON,
            # don't crash the program.
            return {
                "error": "parse_failed",
                "raw_output": raw
            }

    except Exception as e:

        return {
            "error": f"AI service error: {str(e)}"
        }