# 🧠 GitHub Developer Skill Intelligence Platform

An ML-powered system that analyzes GitHub profiles and estimates developer skill levels, strengths, and activity using repository analytics and machine learning.
**#Description**
Architected a full-stack system that evaluates developer proficiency using machine learning and GitHub analytics
Created a feature engineering pipeline extracting behavioral and repository-level insights (activity, popularity, language diversity)
Trained a RandomForest/XGBoost model on 2,000+ synthetic profiles to generate reliable skill predictions
Built a high-performance FastAPI service with async GitHub data ingestion and REST API (/analyze/{username})
Optimized system performance using database caching (Supabase), reducing redundant API calls and improving response time
Developed a modern UI dashboard (Next.js + Tailwind) for intuitive visualization of developer metrics

## 📊 ML Model

- **Algorithm**: RandomForestRegressor (or XGBoost if installed)
- **Training data**: 2,000 synthetic developer profiles with domain-calibrated skill scores
- **Features**: 21 engineered features across repos, languages, activity, and community
- **Output**: Skill score 0.0–10.0 with tier classification (Beginner/Intermediate/Advanced/Expert)
- **Test MAE**: ~0.45 on held-out synthetic data
