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
