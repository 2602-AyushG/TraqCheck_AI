import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

REQUEST_PROMPT = """You are an HR assistant. Write a short, polite email requesting
identity documents (PAN card and Aadhaar card) from a job candidate.

Candidate details:
Name: {name}
Company: {company}
Designation: {designation}

Requirements:
- Keep it under 100 words
- Professional but warm tone
- Explain briefly why the documents are needed (KYC/onboarding compliance)
- Do not include a subject line, just the email body
- Sign off as "HR Team"
"""

def generate_document_request(candidate):
    if not candidate:
        return {"success": False, "error": "candidate data is missing"}
    if not candidate.get("name"):
        return {"success": False, "error": "candidate name is missing"}
    if not candidate.get("company"):
        return {"success": False, "error": "company is missing"}
    if not candidate.get("designation"):
        return {"success": False, "error": "designation is missing"}

    prompt = REQUEST_PROMPT.format(
        name=candidate.get("name"),
        company=candidate.get("company"),
        designation=candidate.get("designation"),
    )

    try:
        response = client.chat.completions.create(
            model="inference-net/schematron-v2-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
    except Exception as e:
        return {"success": False, "error": f"AI service error: {str(e)}"}

    return {"success": True, "text": response.choices[0].message.content.strip()}