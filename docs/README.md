# GitHub Developer Skill Intelligence Platform — MVP

## Quick Start

```bash
# 1. Clone and install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # add GITHUB_TOKEN, SUPABASE_URL, SUPABASE_KEY

# 2. Train the ML model (creates ml_training/saved_model/*.joblib)
python -m ml_training.train_model.train

# 3. Run the API
uvicorn backend.api.main:app --reload --port 8000

# 4. Test
curl http://localhost:8000/api/v1/analyze/torvalds

# 5. Frontend
cd frontend && npm install && npm run dev
```

## Architecture

Frontend (Next.js + TailwindCSS + Chart.js)
    ↓ HTTP
Backend API (FastAPI)
    ↓         ↓            ↓
GitHub     Feature      ML Scorer
Client   Engineering  (RandomForest)
    ↓
Supabase DB

## Folder Structure

```
github-skill-platform/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI app entry
│   │   └── routes.py            # GET /analyze/{username}
│   ├── services/
│   │   ├── github_client.py     # GitHub REST API
│   │   ├── feature_engineering.py
│   │   └── skill_scorer.py      # ML inference + insights
│   └── database/
│       └── db.py                # Supabase CRUD
├── ml_training/
│   ├── saved_model/             # joblib artifacts
│   └── train_model/
│       └── train.py             # training + evaluation
├── frontend/
│   ├── pages/index.jsx
│   ├── components/
│   └── charts/
├── requirements.txt
├── .env.example
└── docs/README.md
```
