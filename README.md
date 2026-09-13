# AI CareerMatch — Intelligent Job Matching & Career Gap Analysis Platform

AI CareerMatch is an intelligent career-technology platform designed for students and technical professionals. It provides transparent, mathematically explainable job matching, actionable skill gap analysis, an interactive "What-If" career simulator, and a personalized, prerequisite-aware career roadmap.

## 🛠️ Technology Stack
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts, TanStack Query v5, Zustand
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2
- **Database (Phase 2+)**: PostgreSQL 15+, SQLAlchemy 2.0 (async), Alembic migrations
- **AI (Phase 4+)**: Google Gemini API (`gemini-1.5-flash` / `gemini-2.0-flash`) via backend only
- **File Handling**: Local filesystem via Python `pathlib.Path` (`uploads/resumes/`)

## 📁 Repository Structure
```
AI CareerMatch/
├── frontend/             # React + TypeScript + Vite Single Page Application
├── backend/              # Python FastAPI REST API Modular Monolith
├── docs/                 # Architecture and Local Development Guides
│   ├── ARCHITECTURE.md   # Complete system architecture specification
│   └── DEVELOPMENT.md    # Local development runbook and prerequisites
├── data/
│   └── seed/             # Curated jobs and skills datasets (Phase 2+)
├── uploads/
│   └── resumes/          # Local resume PDF storage directory
├── .env.example          # Environment template
└── .gitignore            # Git exclusion rules
```

## 🚀 Getting Started (Phase 1 Local Setup)
See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for complete step-by-step instructions.

### Quick Start
1. **Backend**:
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
2. **Frontend**:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
3. Open `http://127.0.0.1:5173` to view the application shell and live backend health connection.

## 📌 Development Roadmap
- [x] **Phase 0**: Architecture & System Design
- [x] **Phase 1**: Project Foundation & Environment Scaffolding (Current)
- [ ] **Phase 2**: Database Schema & Seed Data Engine
- [ ] **Phase 3**: Authentication & Profile Management
- [ ] **Phase 4**: Resume Processing & AI Extraction Pipeline
- [ ] **Phase 5**: Deterministic Matching Engine & Job Catalog
- [ ] **Phase 6**: Explainable Matching & Skill Gap Analysis
- [ ] **Phase 7**: Interactive What-If Career Simulator
- [ ] **Phase 8**: Personalized Career Roadmap Engine
- [ ] **Phase 9**: Real-Time Analytics & Career Dashboard
- [ ] **Phase 10**: Integration Testing, Polish & Final Validation
