# Integration Testing Guide

## System Status ✅

### Running Services
- **Backend API**: http://localhost:8000 ✓
  - Health check: `/health` 
  - Analytics: `/api/v1/analyze/{username}`
  - API docs: `/docs` (Swagger UI)
  
- **Frontend**: http://localhost:3000 ✓
  - Search page: Home page
  - Profile analysis: `/profile/{username}`

- **ML Model**: Trained and loaded ✓
  - Location: `ml_training/saved_model/`
  - Status: Ready for inference

---

## Testing Checklist

### 1. Configure GitHub Token
To enable full functionality, you need a GitHub Personal Access Token:

1. Go to https://github.com/settings/tokens
2. Create new token (classic)
3. Give it `repo` and `user` scopes
4. Copy the token
5. Edit `backend/.env`:
   ```env
   GITHUB_TOKEN=ghp_your_token_here
   ```
6. Restart the backend server

### 2. Test the API Endpoint
Once GITHUB_TOKEN is set:
```bash
curl http://localhost:8000/api/v1/analyze/octocat
```

Expected response:
```json
{
  "username": "octocat",
  "skill_score": 7.5,
  "language_breakdown": { "Python": 5, "JavaScript": 3 },
  "strengths_weaknesses": { 
    "strengths": ["..."], 
    "weaknesses": ["..."] 
  },
  "code_metrics": { "repo_count": 8, ... },
  "activity_level": "active"
}
```

### 3. Test the Frontend
1. Visit http://localhost:3000
2. Enter a GitHub username (e.g., "octocat")
3. Click "Analyze Profile →"
4. Verify the profile page loads with:
   - ✅ Skill score card
   - ✅ Language breakdown chart
   - ✅ Strengths/weaknesses
   - ✅ Key metrics

### 4. Test Caching (Optional)
Once Supabase is configured:
1. Search for same username twice
2. Second request should be instant (cached)

---

## Troubleshooting

### Backend won't start
```bash
# Check Python environment
python -m pip list | grep -E "fastapi|uvicorn|joblib"

# Restart server
cd backend && python -m uvicorn main:app --reload
```

### Frontend shows "Analyzing..." forever
- Check backend is running: http://localhost:8000/health
- Check browser console for CORS errors
- Verify `NEXT_PUBLIC_API_URL` is correct

### API returns 401 Unauthorized
- Set valid GITHUB_TOKEN in `backend/.env`
- Restart backend server

### Charts not showing in profile page
- Check if API returned `language_breakdown` and `code_metrics`
- Verify Chart.js is installed: `npm list chart.js`

---

## Next Steps

### For Production
1. ✅ Configure Supabase (see `SUPABASE_SETUP.md`)
2. Build frontend: `npm run build`
3. Deploy to Vercel, Netlify, or your platform
4. Configure CORS in backend for production domain
5. Add authentication and rate limiting
6. Monitor API usage and model performance

### For Development
- The system is ready for local testing
- You can modify pages, add features, and test immediately
- Hot reload is enabled for both frontend and backend

---

## API Endpoints

### GET /health
Health check endpoint.
**Response**: `{ "status": "healthy", "service": "github-skill-platform" }`

### GET /api/v1/analyze/{username}
Analyze a GitHub user's profile.
**Query params**: (none)
**Response**:
```json
{
  "username": "string",
  "skill_score": "float (0-10)",
  "language_breakdown": "object",
  "strengths_weaknesses": "object",
  "code_metrics": "object",
  "activity_level": "string"
}
```
**Errors**:
- 404: User not found
- 401: Invalid GitHub token
- 500: Internal server error

---

**System is ready for testing! 🚀**
