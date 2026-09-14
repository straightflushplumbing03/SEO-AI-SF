-- ============================================================================
-- SFGE - Straight Flush Growth Engine  (schema.sql)
-- PostgreSQL-compatible DDL. Also valid as a plain-SQL statement set for
-- SQLite (integer PRIMARY KEY, TEXT, REAL, no enums / no deferred FK tricks).
--
-- Key privacy rule: `jobs` stores NO exact addresses, NO customer names, and
-- NO exact prices. Cost is bucketed; location is city + neighborhood only.
-- ============================================================================

CREATE TABLE IF NOT EXISTS jobs (
    job_id              INTEGER PRIMARY KEY,
    date                TEXT,               -- ISO date YYYY-MM-DD
    city                TEXT NOT NULL,
    neighborhood        TEXT,
    service_type        TEXT NOT NULL,      -- e.g. "Slab Leak Detection"
    issue_description   TEXT NOT NULL,
    photos              TEXT,               -- JSON array of filenames (public-safe images)
    duration_hours      REAL,
    cost_range_bucket   TEXT,               -- e.g. "15001-25000" (never an exact price)
    customer_quote      TEXT,               -- plain-language quote (optional, with consent)
    review_id           INTEGER,            -- FK -> reviews.review_id (nullable)
    published_content_id INTEGER,           -- FK -> content.content_id (nullable)
    status              TEXT DEFAULT 'logged',  -- logged | generated | approved | done
    created_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id              INTEGER PRIMARY KEY,
    job_id                 INTEGER,         -- FK -> jobs.job_id (nullable)
    source                 TEXT NOT NULL,   -- 'google' | 'yelp' | 'sms' | 'email' | ...
    rating                 INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    text                   TEXT NOT NULL,
    sentiment              TEXT,            -- positive | neutral | negative
    extracted_keywords     TEXT,            -- JSON array
    extracted_city         TEXT,
    extracted_service      TEXT,
    approved_for_publish   INTEGER DEFAULT 0,
    published              INTEGER DEFAULT 0,
    created_at             TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS opportunities (
    opp_id              INTEGER PRIMARY KEY,
    keyword             TEXT NOT NULL,
    city                TEXT,
    service_type        TEXT,
    search_volume       INTEGER,
    difficulty          REAL,
    intent_type         TEXT,               -- informational | commercial | emergency
    ai_visibility_gap_flag INTEGER DEFAULT 0,
    status              TEXT DEFAULT 'open',  -- open | queued | generated | done
    priority_score      REAL DEFAULT 0.0,
    url                 TEXT,               -- where the result lands (page URL)
    created_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS content (
    content_id       INTEGER PRIMARY KEY,
    type             TEXT NOT NULL,          -- 'case_study' | 'city_page' | 'service_page' | 'blog' | 'faq' ...
    tier             TEXT,                   -- 'tier1' | 'tier2'
    city             TEXT,
    service_type     TEXT,
    source_job_ids   TEXT,                   -- JSON array of jobs.job_id
    site_path        TEXT,                   -- e.g. case-studies/laguna-niguel-slab-leak-001.html
    canonical_url    TEXT,
    title            TEXT,
    schema_types     TEXT,                   -- JSON array: ["Article","BreadcrumbList","FAQPage","Review"]
    publish_status   TEXT DEFAULT 'pending_approval',  -- pending_approval | pr | live
    pr_url           TEXT,
    live_url         TEXT,
    needs_field_data INTEGER DEFAULT 0,      -- Tier-2 pages flagged for upgrade
    created_at       TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ai_visibility_checks (
    check_id          INTEGER PRIMARY KEY,
    date              TEXT,
    prompt            TEXT NOT NULL,
    engine            TEXT NOT NULL,         -- chatgpt | perplexity | gemini | google_ai_overview
    cited             INTEGER DEFAULT 0,
    competitors_cited TEXT,                  -- JSON array
    source_urls_pulled TEXT,                 -- JSON array
    notes             TEXT,
    created_at        TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_findings (
    finding_id   INTEGER PRIMARY KEY,
    date         TEXT,
    category     TEXT,      -- cwv | links | canonical | sitemap | schema | images | mobile
    severity     TEXT,      -- low | medium | high
    message      TEXT,
    url          TEXT,
    auto_fixed   INTEGER DEFAULT 0,
    pr_url       TEXT,
    created_at   TEXT DEFAULT (datetime('now'))
);

-- Convenience indexes
CREATE INDEX IF NOT EXISTS idx_jobs_city       ON jobs (city);
CREATE INDEX IF NOT EXISTS idx_jobs_service    ON jobs (service_type);
CREATE INDEX IF NOT EXISTS idx_reviews_job     ON reviews (job_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_city ON opportunities (city);
CREATE INDEX IF NOT EXISTS idx_content_city    ON content (city);