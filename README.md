# TraqCheck AI

An AI-powered candidate onboarding system. HR uploads a resume, the system extracts structured candidate details with an LLM, then an AI agent generates a personalized request for PAN and Aadhaar documents, and the candidate's submissions are tracked.

## Live Demo

- **Frontend:** https://traq-check-ai.vercel.app
- **Backend API:** https://traqcheck-ai.onrender.com

> The backend runs on Render's free tier. The first request after inactivity can take 30–60 seconds while the instance wakes up. Data stored on the free instance (SQLite and uploaded files) is **not persistent** and may be reset on restart or redeploy.

## Features

- Drag-and-drop resume upload (PDF or DOCX) with upload progress
- Resume text extraction (pdfplumber, python-docx)
- LLM-based extraction of name, email, phone, company, designation and skills, with per-field confidence scores
- Candidate dashboard (name, email, company, extraction status)
- Candidate profile view showing extracted data and confidence
- One-click AI-generated, personalized document request (PAN / Aadhaar), stored against the candidate
- Upload and view submitted PAN / Aadhaar images
- Status tracking per candidate

## Architecture

```text
                 ┌─────────────────────┐
                 │   React Frontend    │
                 │   (Vite, Vercel)    │
                 └──────────┬──────────┘
                            │ REST (JSON / multipart)
                            ▼
                 ┌─────────────────────┐
                 │   Flask Backend     │
                 │      (Render)       │
                 └──────────┬──────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
   │ PDF / DOCX  │   │   SQLite    │   │ OpenRouter  │
   │ text extract│   │  database   │   │  LLM (free) │
   └─────────────┘   └─────────────┘   └─────────────┘
```

**Modules (backend):**

| File | Responsibility |
|---|---|
| `app.py` | Flask app, routes, validation, CORS |
| `parser.py` | Text extraction from PDF/DOCX and LLM-based field extraction |
| `agent.py` | Generates the personalized PAN/Aadhaar request message |
| `db.py` | SQLite schema and helpers |

## Tech Stack

- **Frontend:** React, Vite, JavaScript, CSS (deployed on Vercel)
- **Backend:** Python, Flask, Flask-CORS, SQLite (deployed on Render)
- **AI:** OpenRouter (NVIDIA Nemotron free model) through the OpenAI-compatible Python SDK. The agent is a custom prompt-driven pipeline; LangChain is not used.
- **Document processing:** pdfplumber, python-docx

## Workflow

1. **Upload:** HR uploads a PDF/DOCX resume.
2. **Extract:** text is pulled from the file and sent to the LLM, which returns structured JSON (name, email, phone, company, designation, skills, confidence).
3. **Store:** the candidate is saved in SQLite with status `parsed`.
4. **Request documents:** the agent writes a personalized message asking for PAN and Aadhaar. The message is stored and logged against the candidate. It is **not** actually sent by email or SMS.
5. **Submit documents:** PAN and/or Aadhaar images are uploaded and the candidate's status is updated to `documents_submitted`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/candidates/upload` | Upload and parse a resume (multipart, field name: `file`) |
| GET | `/candidates` | List all candidates |
| GET | `/candidates/<id>` | Parsed profile with extracted data |
| POST | `/candidates/<id>/request-documents` | Generate and log an AI document request |
| POST | `/candidates/<id>/submit-documents` | Upload PAN and/or Aadhaar images |

## Local Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
OPENROUTER_API_KEY=your_api_key_here
```

Initialize the database and run:

```bash
python db.py
python app.py
```

Backend runs at `http://127.0.0.1:5000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`. Set the backend URL in the frontend environment/config (see `frontend/src/api.js`).

## Project Structure

```text
TraqCheck_AI/
├── backend/
│   ├── app.py
│   ├── agent.py
│   ├── parser.py
│   ├── db.py
│   ├── requirements.txt
│   ├── uploads/
│   └── documents/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## Design Decisions

- **Flask + SQLite:** minimal setup for a time-boxed assignment; schema is simple and easy to migrate to PostgreSQL.
- **OpenRouter free model:** the assignment allowed any free model. Trade-off: free models can be slow or rate-limited.
- **Custom agent instead of LangChain:** the agent's job is a single, well-defined generation step, so a direct SDK call keeps the code small and easy to debug.
- **Request is logged, not sent:** matches the brief ("generates and logs"). Real delivery would plug in an email/WhatsApp provider.

## Known Limitations

- **No authentication or authorization.** Candidate IDs are sequential and endpoints are open, so anyone with the URL can access candidate data and uploaded documents. This is not acceptable for real PAN/Aadhaar data.
- **PAN/Aadhaar are stored as plain uploaded files** with no encryption, masking, or retention policy.
- **No OCR or validation of the uploaded documents.** The system does not check that a file is actually a PAN or Aadhaar card, nor validate number formats.
- **Scanned / image-only resumes are not supported** (no OCR). Text in DOCX headers, tables or text boxes may be missed.
- **Confidence scores come from the LLM's output** and are indicative, not calibrated.
- **Free-tier hosting:** SQLite and uploaded files are ephemeral on Render; cold starts are slow.
- **LLM calls are synchronous**, so a slow or rate-limited model slows the upload request.
- No pagination or search on the candidate list.

## Future Improvements

- PostgreSQL and persistent object storage (S3 or similar)
- Authentication, role-based access, signed document URLs, encryption at rest
- Actual delivery of document requests via email/WhatsApp
- Background job queue for parsing
- OCR for scanned resumes and document verification (PAN/Aadhaar format and card detection)
- Duplicate detection, pagination and search
- Prompt-injection hardening for resume content
- Audit logging and monitoring

## Author

**Ayush Gupta**
B.Tech, Delhi Technological University
