-- 0001_initial_schema.sql
-- ベースとなるテーブル定義を作成

BEGIN;

CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    initial_handicap NUMERIC(5,2) NOT NULL DEFAULT 0,
    affiliation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE TABLE IF NOT EXISTS competitions (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    date DATE NOT NULL,
    location TEXT,
    course TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'planned',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    CONSTRAINT competitions_status_check CHECK (status IN ('planned','ongoing','completed','cancelled'))
);

CREATE TABLE IF NOT EXISTS participants (
    id SERIAL PRIMARY KEY,
    competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    UNIQUE (competition_id, player_id)
);

CREATE TABLE IF NOT EXISTS scores (
    id SERIAL PRIMARY KEY,
    competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    course TEXT,
    out_score INTEGER,
    in_score INTEGER,
    handicap NUMERIC(5,2) DEFAULT 0,
    net_score NUMERIC(6,2),
    ranking INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    UNIQUE (competition_id, player_id)
);

CREATE TABLE IF NOT EXISTS announcements (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    image_url TEXT,
    tournament_info JSONB,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE TABLE IF NOT EXISTS backups (
    id SERIAL PRIMARY KEY,
    backup_id TEXT NOT NULL UNIQUE,
    backup_date TEXT NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_scores_competition ON scores (competition_id);
CREATE INDEX IF NOT EXISTS idx_scores_player ON scores (player_id);
CREATE INDEX IF NOT EXISTS idx_participants_competition ON participants (competition_id);
CREATE INDEX IF NOT EXISTS idx_participants_player ON participants (player_id);
CREATE INDEX IF NOT EXISTS idx_announcements_active ON announcements (is_active, display_order DESC);

COMMIT;
