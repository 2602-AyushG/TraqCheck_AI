````markdown
# TraqCheck AI

An AI-powered candidate onboarding system that automates resume parsing, candidate information extraction, document requests, and document submission.

## 🚀 Live Demo

**Frontend:**  
https://traq-check-ai.vercel.app

**Backend API:**  
https://traqcheck-ai.onrender.com

## ✨ Features

- Upload candidate resumes in PDF or DOCX format
- Extract resume text automatically
- Use an LLM to extract structured candidate information
- Store candidate information in SQLite
- Display candidates through a React frontend
- Generate personalized document-request messages using AI
- Upload PAN and Aadhaar documents
- Track candidate onboarding status

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │   React Frontend    │
                    │      Vercel         │
                    └──────────┬──────────┘
                               │ REST API
                               ▼
                    ┌─────────────────────┐
                    │   Flask Backend     │
                    │      Render         │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
      ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
      │ PDF/DOCX    │   │   SQLite    │   │ OpenRouter  │
      │ Extraction  │   │  Database   │   │     LLM     │
      └─────────────┘   └─────────────┘   └─────────────┘
````

## 🛠️ Tech Stack

### Frontend

* React.js
* Vite
* JavaScript
* CSS

### Backend

* Python
* Flask
* Flask-CORS
* SQLite

### AI

* OpenRouter
* NVIDIA Nemotron 3 Super
* OpenAI-compatible Python SDK

### Document Processing

* pdfplumber
* python-docx

### Deployment

* Vercel — Frontend
* Render — Backend

## 🔄 Workflow

### 1. Resume Upload

A recruiter uploads a candidate's PDF or DOCX resume.

```text
Resume
   ↓
File Upload
   ↓
Text Extraction
   ↓
LLM Processing
   ↓
Structured Candidate Data
```

The system extracts:

* Name
* Email
* Phone
* Company
* Designation
* Skills
* Extraction confidence

### 2. Candidate Storage

The extracted information is stored in SQLite.

Each candidate receives a unique ID and an onboarding status.

Example:

```json
{
  "name": "AYUSH GUPTA",
  "email": "ayushg2602@gmail.com",
  "company": "Oracle",
  "designation": "Software Developer Intern",
  "status": "parsed"
}
```

### 3. Document Request

The recruiter can request onboarding documents.

The AI generates a personalized request containing the required documents such as:

* PAN card
* Aadhaar card

The generated request is stored against the candidate.

### 4. Document Submission

The candidate can upload:

* PAN
* Aadhaar

The submitted document metadata is stored and the candidate status is updated to:

```text
documents_submitted
```

## 📡 API Endpoints

### Health Check

```http
GET /
```

Checks whether the backend is running.

### Upload Resume

```http
POST /candidates/upload
```

Uploads and parses a PDF/DOCX resume.

### List Candidates

```http
GET /candidates
```

Returns all candidates.

### Get Candidate

```http
GET /candidates/<candidate_id>
```

Returns detailed candidate information.

### Request Documents

```http
POST /candidates/<candidate_id>/request-documents
```

Generates an AI-powered document request.

### Submit Documents

```http
POST /candidates/<candidate_id>/submit-documents
```

Uploads PAN and/or Aadhaar documents.

## 📁 Project Structure

```text
candidate-ai-system/
│
├── backend/
│   ├── app.py
│   ├── agent.py
│   ├── parser.py
│   ├── db.py
│   ├── requirements.txt
│   ├── uploads/
│   └── documents/
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

## ⚙️ Local Setup

### Backend

```bash
cd backend

python3 -m venv venv312
source venv312/bin/activate

pip install -r requirements.txt
```

Create a `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here
```

Initialize the database:

```bash
python db.py
```

Run the backend:

```bash
python app.py
```

Backend will run at:

```text
http://127.0.0.1:5000
```

### Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at:

```text
http://localhost:5173
```

## 🔐 Environment Variables

The backend requires:

```env
OPENROUTER_API_KEY=your_api_key_here
```

The API key should never be committed to GitHub.

## 📌 Current Limitations

* SQLite is used for simplicity and demonstration purposes.
* The Render free instance may take some time to wake up after inactivity.
* Uploaded files and SQLite data on the free Render filesystem are not suitable for production-grade persistent storage.
* Production deployment would use persistent object storage and a managed database.
* Authentication and role-based access control are not currently implemented.

## 🔮 Future Improvements

* PostgreSQL or another managed database
* Persistent object storage for candidate documents
* Authentication and role-based access control
* Candidate search and filtering
* Resume scoring and job-description matching
* Automated email delivery
* Document verification
* Audit logging
* Production-grade monitoring

## 👨‍💻 Author

**Ayush Gupta**

B.Tech — Software Engineering
Delhi Technological University

---

Built as an AI-powered candidate onboarding workflow combining document processing, LLM-based extraction, REST APIs, and cloud deployment.

````

### Then save and push

From your project root:

```bash
git add README.md
git commit -m "Add project documentation"
git push origin main
````

**No Render redeployment is needed for a README-only change.** Your live application will remain exactly as it is.
