# AI CareerMatch — Local Development Guide

## 1. Prerequisites
Before running AI CareerMatch locally, ensure you have the following installed on your Windows environment:
- **Node.js**: v20+ LTS or v24+ (verified with `node -v` and `npm -v`)
- **Python**: v3.11, v3.12, or v3.13 (verified with `python --version` and `pip --version`)
- **Git**: v2.40+ (verified with `git --version`)
- **PostgreSQL**: v15, v16, or v17 (Required for database persistence foundation)

---

## 2. PostgreSQL Database Setup & Configuration
AI CareerMatch uses local PostgreSQL via `asyncpg` and SQLAlchemy 2.0.

### A. Environment Configuration (`backend/.env`)
Verify the database connection string in `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_careermatch_db
```
*(Replace `postgres:postgres` with your local PostgreSQL username and password if different).*

### B. Database Initialization (One-time)
When PostgreSQL is running on your machine, connect to your PostgreSQL instance (e.g. via `psql` or pgAdmin) and ensure the database exists:
```sql
CREATE DATABASE ai_careermatch_db;
```

### C. Running Alembic Migrations
Apply the initial schema migration to create all 18 domain tables:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
```

### D. Running Idempotent Seed Data
Populate the 45 standardized skills, 15 aliases, 15 explicit relationships, 21 prerequisites, and 42 curated job postings:
```powershell
python -m app.data.seed_data
```
*(This seed script is fully idempotent and can be safely re-run without creating duplicate records).*

---

## 3. Starting the Backend Locally

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Start Uvicorn development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- **Backend API Base**: `http://127.0.0.1:8000`
- **Service Health Check**: `http://127.0.0.1:8000/api/v1/health`
- **Database Health Check**: `http://127.0.0.1:8000/api/v1/health/db`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`

---

## 4. Starting the Frontend Locally

```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Start Vite dev server
npm run dev
```
- **Frontend App URL**: `http://127.0.0.1:5173`

---

## 5. Running the Test Suite

Execute the backend test suite:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest tests
```
The test suite validates:
- Service health and database readiness probe (`tests/test_health.py`)
- All 18 domain models and schema constraints (`tests/test_models.py`)
- Taxonomy, relationships, prerequisites, and job seed data integrity (`tests/test_seeds.py`)
- Alembic migration script consistency (`tests/test_migrations.py`)

---

## 6. Troubleshooting PostgreSQL on Windows

If `GET /api/v1/health/db` returns status `unavailable` with HTTP 503:
1. **Check if PostgreSQL service is running**:
   ```powershell
   Get-Service | Where-Object { $_.Name -like "*postgres*" }
   ```
2. **Start the PostgreSQL service**:
   ```powershell
   Start-Service postgresql-x64-17  # (or your version service name)
   ```
3. **Verify Port 5432 is listening**:
   ```powershell
   netstat -ano | findstr :5432
   ```
4. **Verify credentials**: Confirm the user and password in `backend/.env` match your local PostgreSQL superuser credentials.

---

## 7. Phase 3: Authentication & Career Profile API Endpoints

### A. Authentication Configuration & Environment Variables
Configured in `backend/.env`:
```env
# Security & JWT Tokens
SECRET_KEY=your_secure_random_key_minimum_32_characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### B. Available Endpoints
- **User Registration**: `POST /api/v1/auth/register`
  - Body: `{"email": "user@example.com", "password": "SecurePassword123!", "full_name": "Jane Doe"}`
  - Status: `201 Created`
  - Returns: `access_token`, `token_type`, `expires_in`, `user` (id, email, full_name, is_active, created_at)
- **User Login**: `POST /api/v1/auth/login`
  - Body: `{"email": "user@example.com", "password": "SecurePassword123!"}`
  - Status: `200 OK`
  - Returns: `access_token`, `token_type`, `expires_in`, `user`
- **Current Authenticated User**: `GET /api/v1/auth/me`
  - Headers: `Authorization: Bearer <access_token>`
  - Status: `200 OK`
- **Get Career Profile**: `GET /api/v1/profile`
  - Headers: `Authorization: Bearer <access_token>`
  - Status: `200 OK` (Returns profile JSON or `null` if not yet configured)
- **Upsert Career Profile**: `PUT /api/v1/profile` (also `PATCH /api/v1/profile`)
  - Headers: `Authorization: Bearer <access_token>`
  - Body:
    ```json
    {
      "target_role": "Senior Cloud Architect",
      "headline": "Distributed Systems & Kubernetes Specialist",
      "bio": "Extensive experience in high-throughput microservices and relational design.",
      "target_location": "Remote, Global",
      "target_employment_type": "Full-time",
      "total_experience_years": 5.5
    }
    ```
  - Status: `200 OK`
  - Returns: Saved `CandidateProfile` with user details

### C. Running Phase 3 Tests
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest tests/test_auth.py tests/test_profile.py -v
```
Validates:
- Bcrypt password salting and hashing security (never plain-text)
- Duplicate email registration rejection (`409 Conflict`)
- Case-insensitive login with correct credentials
- Bad credential rejection (`401 Unauthorized`)
- JWT authentication dependency and token validation
- Career Profile initial empty state, creation, and updates
- Strict user data isolation (User A cannot view or edit User B's profile)
- Negative experience constraint enforcement (`422 Unprocessable Entity`)

---

## 8. Phase 4: Resume PDF Upload + AI Extraction + Staging Review

### A. Environment Configuration (`backend/.env`)
Set the Gemini API key to enable live structured AI extraction:
```env
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```
*(Note: If `GEMINI_API_KEY` is not provided, the upload and PDF extraction succeed, and the resume status is set to `failed` with a clear explanation rather than crashing or hallucinating).*

### B. Upload Invariants & Security
- **Max File Size**: 10 MB (`MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024`)
- **MIME & Header Check**: Requires `application/pdf` MIME type and `%PDF-` magic header bytes.
- **Pure-Python Text Extraction**: Ingested via `pypdf.PdfReader` with scanned/image-only PDF detection (< 50 alphanumeric characters).
- **Safe Storage**: Saved with a generated UUID filename in `uploads/resumes/` to prevent directory traversal or file collision.

### C. Available Endpoints
- **Upload & Extract Resume**: `POST /api/v1/resumes`
  - Headers: `Authorization: Bearer <token>`
  - Body: `multipart/form-data` with `file: <resume.pdf>`
  - Status: `201 Created`
  - Returns: `ResumeDetailResponse` with status `pending_review` and `parsed_staging_json`
- **List Resumes**: `GET /api/v1/resumes`
  - Headers: `Authorization: Bearer <token>`
  - Status: `200 OK`
  - Returns: `List[ResumeResponse]` scoped strictly to authenticated user
- **Get Resume Detail & Staging Draft**: `GET /api/v1/resumes/{id}`
  - Headers: `Authorization: Bearer <token>`
  - Status: `200 OK`
  - Returns: `ResumeDetailResponse` with `parsed_staging_json`
- **Delete Resume**: `DELETE /api/v1/resumes/{id}`
  - Headers: `Authorization: Bearer <token>`
  - Status: `200 OK`
  - Cleans up database record and safely deletes the uploaded file from disk
- **Apply Staged Resume to Profile**: `POST /api/v1/resumes/{id}/apply`
  - Headers: `Authorization: Bearer <token>`
  - Body: `StructuredResumeData` (edited and confirmed by candidate)
  - Status: `200 OK`
  - Transactionally creates/updates:
    - `candidate_profiles` (headline, bio, target_role, total_experience_years)
    - `candidate_skills` (mapped canonical skills or custom candidate skills with verification flag)
    - `educations`, `experiences`, `projects`, and `certifications`

### D. Running Phase 4 Tests
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest tests/test_resumes.py -v
```
Validates:
- Unauthenticated upload rejection (`401 Unauthorized`)
- Non-PDF extension rejection (`400 Bad Request`)
- Spoofed PDF magic header rejection (`400 Bad Request`)
- Empty file rejection (`400 Bad Request`)
- Oversized file rejection (`413 Payload Too Large`)
- Authenticated PDF text extraction and Gemini structured extraction mock
- Canonical skill taxonomy matching (exact match, alias normalization, custom unmatched)
- Graceful handling when Gemini API key is missing
- User data ownership isolation
- Transactional application of staged draft to candidate profile and sub-tables
- Resume deletion and safe disk file cleanup

