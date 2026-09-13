# AI CareerMatch — Approved Technical Architecture

## 1. System Overview & Core Philosophy
AI CareerMatch is a career-technology web application engineered to bridge the divide between a candidate's actual qualifications and target market expectations. The core philosophy centers on:
1. **Deterministic & Explainable Matching**: Numerical match scores, skill gap classifications, and simulation deltas are calculated through a pure, rule-based mathematical engine.
2. **AI Enrichment Only**: Large Language Models (Google Gemini) are strictly used for unstructured resume extraction, recruiter-style explanatory narratives, and learning task suggestions. Gemini **never** calculates or alters numeric scores.
3. **User-in-the-Loop Ingestion**: Resume PDF extraction outputs into an interactive staging review modal before database persistence.
4. **Local Windows Autonomy**: The platform runs 100% locally on standard tooling (Python 3.11/3.12/3.13, Node.js 20+, PostgreSQL 15/16/17) without external cloud or proprietary proxy dependencies.

---

## 2. Technology Stack
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts, TanStack Query v5, Zustand.
- **Backend**: Python, FastAPI, Uvicorn, Pydantic v2, Pydantic Settings.
- **Database (Phase 2+)**: PostgreSQL (relational schema), SQLAlchemy 2.0 (asyncio with asyncpg), Alembic migrations.
- **AI (Phase 4+)**: Official Google Gemini API (`gemini-1.5-flash` / `gemini-2.0-flash`) via backend SDK only.
- **File Storage**: Local filesystem via Python `pathlib.Path` in `uploads/resumes/`.

---

## 3. High-Level Architecture (Modular Monolith)
```
+-------------------------------------------------------------+
|                        FRONTEND SPA                         |
|   React + TypeScript + Vite + Tailwind CSS + Lucide Icons   |
|   State: TanStack Query v5 (Server) + Zustand (Client)      |
+------------------------------+------------------------------+
                               | HTTP REST (/api/v1)
                               v
+-------------------------------------------------------------+
|                     BACKEND API (FastAPI)                   |
|   Routers: Auth, Profile, Resumes, Jobs, Matching,          |
|            Simulator, Roadmaps, Dashboard                   |
+----+--------------------+--------------------+--------------+
     |                    |                    |
     v                    v                    v
+-----------+       +-----------+       +--------------+
| AI Service|       | Matching  |       | Data Access  |
|  (Gemini) |       |  Engine   |       | (SQLAlchemy) |
+-----------+       +-----------+       +-------+------+
                                                |
                                                v
                                        +--------------+
                                        |  PostgreSQL  |
                                        |   Database   |
                                        +--------------+
```

---

## 4. Deterministic Matching Engine Specification
The overall score $S_{\text{overall}} \in [0.00, 100.00]$ is a weighted sum of four discrete alignment dimensions:
$$S_{\text{overall}} = (w_{\text{req}} \cdot S_{\text{req}}) + (w_{\text{pref}} \cdot S_{\text{pref}}) + (w_{\text{exp}} \cdot S_{\text{exp}}) + (w_{\text{edu}} \cdot S_{\text{edu}})$$

### Dynamic Proportional Weight Redistribution
- **Base Weights**: Required Skills ($0.50$), Preferred Skills ($0.20$), Experience ($0.20$), Education ($0.10$).
- If a dimension has no applicable data (e.g. no preferred skills listed), its weight is redistributed proportionally across remaining active dimensions $A$:
  $$w_d = \frac{w_d^0}{\sum_{k \in A} w_k^0}$$
  Guaranteeing: $\sum_{d \in A} w_d \equiv 1.000$.

### Explicit Skill Relationships & Proficiency
- Exact alias match $\implies \alpha = 1.00$.
- Configured transferable skill $\implies$ stored $\alpha \in (0.0, 1.0)$.
- Unconfigured skill $\implies \alpha = 0.00$ (zero partial credit).
- Proficiency levels: Beginner (Rank 1), Intermediate (Rank 2), Advanced (Rank 3), Expert (Rank 4).
- Source tracking: `user_verified` ($K=1.00$), `resume_inferred` ($K=0.90$), `unknown` ($P=0.50$ baseline, not assumed intermediate).

### Education Compatibility Matrix
Hierarchical ranks (None: 0, High School: 1, Associate: 2, Bachelor: 3, Master: 4, Doctorate: 5). If candidate rank $<$ job minimum rank, explicit lookup in compatibility matrix $C(R_{\text{cand}}, R_{\text{job}})$. Field alignment multiplier $F_{\text{field}} \in [0.65, 1.00]$.

---

## 5. Architectural Invariants
1. Final match score must always be bounded: $0.00 \le S \le 100.00$.
2. Active scoring weights must always sum to exactly $1.000$.
3. Same inputs must always produce the identical score.
4. Gemini must never determine or modify the numeric score.
5. The identical scoring engine is reused by normal job matching, cached evaluations, and the What-If Career Simulator.
## 6. Persistence Architecture & Schema Rules (Phase 2)
The database persistence foundation implements all 18 domain models under PostgreSQL:

### A. Entity Domain Inventory
1. `users`: Core identity credentials.
2. `candidate_profiles`: Primary profile bio, targets, and total experience.
3. `skills`: Master taxonomy of technical skills.
4. `skill_aliases`: Canonical normalization dictionary (e.g. Postgres -> PostgreSQL).
5. `skill_relationships`: Explicit transferable and related pairs with `similarity_weight` in (0, 1]. Sole source for partial match credit.
6. `skill_prerequisites`: Explicit dependencies with `difficulty_tier` in [1, 5] for roadmap DAG ordering.
7. `candidate_skills`: Candidate-held skills with `proficiency_level` and `proficiency_source` ('user_verified', 'resume_inferred', 'unknown').
8. `education`: Academic degrees, institutions, GPA, and dates.
9. `experience`: Employment history, responsibilities, and JSONB technologies.
10. `projects`: Portfolio projects, repository URLs, and JSONB technologies.
11. `certifications`: Industry certifications and credential URLs.
12. `resumes`: PDF file records and parsed staging JSON awaiting confirmation.
13. `jobs`: Internal curated catalog of positions with experience and education criteria.
14. `job_skills`: Required and preferred skills with weights in [0.5, 2.0].
15. `job_matches`: Persisted mathematical scores, breakdown JSON, and AI explanation.
16. `roadmaps`: Personalized roadmap targets and completion counts.
17. `roadmap_items`: Ordered roadmap milestone units with status tracking.
18. `candidate_activity`: Real-time user interaction audit trail.

### B. Cascades & Master Integrity
- Deleting a `User` cascades to delete their `CandidateProfile`, `Resumes`, and `CandidateActivity`.
- Deleting a `CandidateProfile` cascades to delete their profile skills, education, experience, projects, certifications, matches, and roadmaps.
- Deletion of shared master entities (`Skill`, `Job`) from candidate-facing tables uses `ON DELETE RESTRICT` to prevent accidental loss of master catalog data.
