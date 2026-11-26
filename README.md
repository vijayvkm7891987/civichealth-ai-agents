# CivicHealth AI — Dual-Agent Public Health Platform

Interactive **Citizen / Customer Portal** and **Frontline Officer & Field Worker Console** powered by **Gemini 2.5 Flash** (`google-genai` SDK) and **FastAPI**.

## Repository Structure

```text
civichealth-ai-agents/
├── index.html               # Interactive Dual-Persona Web App (GitHub Pages ready)
├── backend/
│   ├── main.py              # FastAPI orchestration server & handoff API
│   ├── agents.py            # Gemini 2.5 Flash agents, prompts & tool loop
│   ├── tools.py             # Citizen & Frontline Python tool definitions
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Google Cloud Run deployment image
├── .gitignore
└── README.md
```

## Quick Start

1. **Public Web UI (GitHub Pages):**
   Enable **Settings -> Pages -> Deploy from a branch (`main` / `root`)** to serve `index.html` publicly.
2. **Backend API (Google Cloud Run):**
   ```bash
   cd backend
   gcloud run deploy civichealth-agents-api \
     --source . \
     --region asia-south1 \
     --allow-unauthenticated \
     --set-env-vars GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
   ```
