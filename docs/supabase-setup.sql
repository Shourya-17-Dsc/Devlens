-- ============================================================
-- GitHub Developer Skill Platform - Supabase Setup Script
-- ============================================================
-- Run this script in your Supabase SQL editor to create
-- the required tables and indexes.
-- 
-- Prerequisites:
--   1. Create a Supabase project at https://supabase.com
--   2. Copy your SUPABASE_URL and SUPABASE_KEY to backend/.env
--   3. Run this script in the SQL editor
-- ============================================================

-- Create analyses table
CREATE TABLE analyses (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      TEXT NOT NULL UNIQUE,
    skill_score   FLOAT,
    feature_vector JSONB,
    result_json   JSONB,
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);

-- Create index on username for faster lookups
CREATE INDEX idx_analyses_username ON analyses(username);

-- Create index on created_at for sorting
CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);

-- Enable Row Level Security (optional but recommended for security)
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow public read access (adjust as needed for your security model)
CREATE POLICY "Enable read access for all users" ON analyses
    FOR SELECT USING (true);

-- Create a policy to allow writes from the API
CREATE POLICY "Enable write access for authenticated users" ON analyses
    FOR INSERT WITH CHECK (true);

-- Create a policy to allow updates
CREATE POLICY "Enable update access for authenticated users" ON analyses
    FOR UPDATE USING (true);

-- ============================================================
-- Optional: Create additional tables for analytics
-- ============================================================

-- Cache recent searches for analytics
CREATE TABLE searches (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      TEXT NOT NULL,
    searched_at   TIMESTAMPTZ DEFAULT now(),
    FOREIGN KEY (username) REFERENCES analyses(username) ON DELETE CASCADE
);

CREATE INDEX idx_searches_searched_at ON searches(searched_at DESC);
