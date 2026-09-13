# AI CareerMatch — Production Deployment Guide

This guide describes how to deploy the **AI CareerMatch** full-stack application (FastAPI backend, React/Vite frontend, PostgreSQL database, and Alembic migrations) to production while keeping your local development environment 100% isolated and safe.

---

## Architecture Overview

| Component | Technology | Production Runtime | Production Build / Start |
|---|---|---|---|
| **Database** | PostgreSQL 16 | Managed Cloud PostgreSQL (Render / Supabase / Neon) | Automated via Alembic migrations & idempotent seed |
| **Backend API** | FastAPI + Python 3.11+ | Uvicorn Web Service | `alembic upgrade head && python -m app.data.seed_data && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Frontend** | React 18 + Vite + TS | Static Site CDN / Edge | `npm install && npm run build` (served from `dist/` with `/* -> /index.html` rewrite) |

---

## Method 1: Deploy with Render Blueprint (Recommended)

Render provides native Infrastructure-as-Code via [render.yaml](file:///c:/Users/Hp/OneDrive/Desktop/AI%20CareerMatch/render.yaml) at the repository root. This provisions all 3 components automatically:

### Step 1: Connect Your GitHub Repository
1. Log into [Render Dashboard](https://dashboard.render.com).
2. Click **New +** in the top navigation and select **Blueprint**.
3. Select and connect your repository: `https://github.com/shraddha-gupta30/AI-CareerMatch.git`.
4. Render will automatically read `render.yaml` and display the blueprint resources:
   - **`ai-careermatch-db`** (Managed PostgreSQL database)
   - **`ai-careermatch-backend`** (FastAPI Web Service)
   - **`ai-careermatch-frontend`** (React/Vite Static Site)

### Step 2: Configure Secrets
Render will ask for any environment variables marked `sync: false`:
- **`GEMINI_API_KEY`**: Paste your Google Gemini API key (for AI resume extraction).

### Step 3: Apply Blueprint
1. Click **Apply**.
2. Render provisions the PostgreSQL database first.
3. When the database is healthy, Render builds the backend, automatically applies `alembic upgrade head`, runs `python -m app.data.seed_data`, and launches Uvicorn.
4. Render builds the frontend and publishes it to `https://ai-careermatch-frontend.onrender.com`.

---

## Method 2: Manual / Modular Cloud Deployment

### 1. Provision Production PostgreSQL
- Provider options: **Render PostgreSQL**, **Neon**, **Supabase**, or **Railway**.
- Obtain your connection URI:
  ```text
  postgresql://user:password@host:port/database_name
  ```
  *(Note: The backend automatically normalizes standard `postgres://` or `postgresql://` connection strings to `postgresql+asyncpg://` at runtime.)*

### 2. Deploy FastAPI Backend Web Service
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Pre-Deploy / Migration Command**: `alembic upgrade head && python -m app.data.seed_data`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  ```env
  APP_ENV=production
  DEBUG=false
  DATABASE_URL=postgresql://user:password@host:port/database_name
  SECRET_KEY=your_production_secret_key_minimum_32_chars
  ALLOWED_ORIGINS=https://your-frontend-domain.com,http://localhost:5173
  GEMINI_API_KEY=your_gemini_api_key
  DB_TIMEOUT=15.0
  UPLOAD_DIR=uploads/resumes
  ```

### 3. Deploy React / Vite Frontend
- **Root Directory**: `frontend`
- **Build Command**: `npm install && npm run build`
- **Publish Directory**: `dist`
- **SPA Rewrites**:
  - Render: Route rule `/* -> /index.html` (defined in `render.yaml`)
  - Vercel: Configured via [frontend/vercel.json](file:///c:/Users/Hp/OneDrive/Desktop/AI%20CareerMatch/frontend/vercel.json)
- **Environment Variables**:
  ```env
  VITE_API_BASE_URL=https://your-backend-domain.com/api/v1
  ```

---

## Post-Deployment Verification Checklist

1. **Backend Health Check**:
   ```bash
   curl -s https://<your-backend-domain>/api/v1/health
   ```
   *Expected Response:*
   ```json
   {
     "status": "healthy",
     "app": "AI CareerMatch",
     "version": "0.1.0",
     "environment": "production",
     "database": {
       "connected": true,
       "status": "healthy"
     }
   }
   ```

2. **Frontend Connectivity**:
   - Open `https://<your-frontend-domain>` in your browser.
   - Navigate to `/jobs` -> Confirm that the 42 curated roles loaded from the production database.
   - Navigate to `/register` -> Create a new user account.
   - Verify that login, profile creation, and skill gap calculations work seamlessly.
