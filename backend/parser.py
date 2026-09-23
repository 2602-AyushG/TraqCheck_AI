import json
import os
import pdfplumber
import docx
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()#ELSE os library wont be able to fetch api key from .env file

def extract_text(file_path):
    if file_path.lower().endswith(".pdf"):
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    elif file_path.lower().endswith(".docx"):
        doc = docx.Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError("Unsupported file format")




client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

#actual prompt that is given to the llm
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
#main function which calls LLM

def parse_resume(resume_text):
    response = client.chat.completions.create(
        model="nvidia/nemotron-3-ultra-550b-a55b:free",
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(resume_text=resume_text)}],
        temperature=0, #so that llm dont uses creAtivity of its own and stick to the prompt given 
    )
    raw = response.choices[0].message.content.strip() # to strip/remove blank spaces if any in start/end
    raw = raw.replace("```json", "").replace("```", "").strip() # replace if json word is there in response(llms do that sometimes)
    try:
        return json.loads(raw) #Converts the JSON text into a Python dictionary.
    except json.JSONDecodeError:
        return {"error": "parse_failed", "raw_output": raw} #If the AI returned invalid JSON, don't crash the program, but return error so app knows AI response was not suitable
