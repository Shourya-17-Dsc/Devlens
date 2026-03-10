# 🧠 GitHub Developer Skill Intelligence Platform

An ML-powered system that analyzes GitHub profiles and estimates developer skill levels, strengths, and activity using repository analytics and machine learning.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js + TailwindCSS)                │
│          Dashboard · Charts · Skill Score · Language Stats           │
└──────────────────────────┬─────────────────────────────────────────┘
                           │ HTTP REST
┌──────────────────────────▼─────────────────────────────────────────┐
│                    Backend API (FastAPI)                              │
│                 GET /api/v1/analyze/{username}                        │
└────────┬──────────────────┬───────────────────┬────────────────────┘
         │                  │                   │
┌────────▼──────┐  ┌────────▼────────┐  ┌───────▼──────────┐
│  GitHub API   │  │  Feature Eng.   │  │   ML Scoring     │
│   Client      │  │  Pipeline       │  │   (RandomForest) │
│               │  │                 │  │                  │
│ /users        │  │ repo_features   │  │ skill_scorer.py  │
│ /repos        │  │ lang_features   │  │ heuristic fallbk │
│ /languages    │  │ activity_feats  │  │ predict 0–10     │
│ /stats/commit │  │ popularity_scr  │  │                  │
└───────────────┘  └─────────────────┘  └──────────────────┘
         │
┌────────▼───────────────────────────────────────────────────────────┐
│                   Supabase (PostgreSQL)                              │
│      developer_analyses  ·  feature_vectors  ·  cached scores       │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
github-skill-platform/
│
├── README.md
├── docs/
│   └── API.md                         ← Full REST API docs
│
├── backend/                           ← FastAPI service
│   ├── main.py                        ← App entry point + CORS
│   ├── requirements.txt
│   ├── .env.example                   ← Copy to .env and fill in
│   │
│   ├── api/
│   │   └── routes.py                  ← GET /analyze/{username}
│   │
│   ├── services/
│   │   ├── github_client.py           ← Async GitHub REST client
│   │   ├── feature_engineering.py     ← Feature extraction pipeline
│   │   └── skill_scorer.py            ← ML model + heuristic fallback
│   │
│   ├── models/
│   │   └── schemas.py                 ← Pydantic data models
│   │
│   └── database/
│       └── db.py                      ← Supabase read/write helpers
│
├── ml_training/                       ← Offline training module
│   ├── train_model/
│   │   └── train.py                   ← Trains + saves model.joblib
│   └── saved_model/                   ← Generated at train time
│       ├── skill_model.joblib
│       ├── scaler.joblib
│       └── model_meta.json
│
└── frontend/                          ← Next.js dashboard
    ├── package.json
    ├── pages/
    │   ├── index.js                   ← Search page
    │   └── profile/[username].js      ← Analysis dashboard page
    └── components/                    ← Chart + UI components
```

---

## 🚀 Quick Start

### 1 — Clone & configure
```bash
git clone https://github.com/you/github-skill-platform.git
cd github-skill-platform
cp backend/.env.example backend/.env
# Edit backend/.env — add your GITHUB_TOKEN and SUPABASE creds
```

### 2 — Train the ML model
```bash
cd ml_training
pip install scikit-learn numpy pandas joblib xgboost
python train_model/train.py
# → Saves saved_model/skill_model.joblib
```

### 3 — Start the backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# → http://localhost:8000/docs (Swagger UI)
```

### 4 — Start the frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 5 — Test the API
```bash
curl http://localhost:8000/api/v1/analyze/torvalds | python -m json.tool
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GITHUB_TOKEN` | Yes | GitHub PAT (5,000 req/hr vs 60 without) |
| `SUPABASE_URL` | No | Supabase project URL for caching |
| `SUPABASE_KEY` | No | Supabase anon key |
| `CACHE_TTL_HOURS` | No | Cache lifetime (default: 6) |

---

## 📊 ML Model

- **Algorithm**: RandomForestRegressor (or XGBoost if installed)
- **Training data**: 2,000 synthetic developer profiles with domain-calibrated skill scores
- **Features**: 21 engineered features across repos, languages, activity, and community
- **Output**: Skill score 0.0–10.0 with tier classification (Beginner/Intermediate/Advanced/Expert)
- **Test MAE**: ~0.45 on held-out synthetic data
