# Supabase Setup Guide

## Overview
The backend API can work without a database, but you'll lose caching functionality. To enable full features with result caching, set up Supabase.

## Steps

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Sign up / Log in
3. Create new project
4. Note your **Project URL** and **Service Role Key** (in Project Settings → API)

### 2. Add Credentials to .env
Edit `backend/.env`:
```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
```

Get these from: **Settings → API → Project URL / anon / Service Role keys**

### 3. Create Database Tables
1. In Supabase dashboard, go to **SQL Editor**
2. Create new query
3. Copy/paste contents of `docs/supabase-setup.sql`
4. Click **Run**

### 4. Verify Connection
```bash
# Restart the backend server
python -m uvicorn backend.main:app --reload
```

You should see:
```
Supabase client initialised
```

## Features Enabled by Supabase
- ✅ Cache analysis results (6 hours TTL)
- ✅ Developer history tracking
- ✅ Search analytics
- ✅ Persistent storage

## Running Without Supabase
The API works fine without Supabase, but:
- ❌ Results are NOT cached (slower for repeat searches)
- ❌ No persistent storage
- ❌ No analytics

Just leave `SUPABASE_URL` and `SUPABASE_KEY` as placeholders.

---

**Next Steps**: Once Supabase is running, restart the backend and you're ready to test the API endpoints!
