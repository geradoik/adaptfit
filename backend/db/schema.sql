-- AdaptFit database schema (SQLite dialect; PostgreSQL port notes in docs/schema-notes.md)
-- Source of truth: ER diagram, Figure 4.3 of the proposal.
-- Safe to run repeatedly: every statement is IF NOT EXISTS.

PRAGMA foreign_keys = ON;
PRAGMA user_version = 3;

CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    email          TEXT    NOT NULL UNIQUE,
    password_hash  TEXT    NOT NULL,
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- FR-4, FR-7, FR-8: one row per profile version. Rows are never updated (see trigger below).
CREATE TABLE IF NOT EXISTS profile_snapshots (
    snapshot_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at         TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    weight             REAL    CHECK (weight IS NULL OR weight > 0),   -- kg
    height             REAL    CHECK (height IS NULL OR height > 0),   -- cm
    sleep_pattern      TEXT,
    training_schedule  TEXT,                                           -- JSON text: {"days": ["mon","wed","fri"]}
    goal               TEXT,
    diet_pattern       TEXT,                                           -- decision D-7 (FR-3)
    -- Changing requirements CR-1..CR-5 (docs/changing-requirements.md). All nullable: a metric that needs a
    -- missing field returns not_enough_data instead of guessing.
    age                INTEGER CHECK (age IS NULL OR (age > 0 AND age < 120)),               -- CR-1
    sex                TEXT    CHECK (sex IS NULL OR sex IN ('male', 'female')),             -- CR-1 (Mifflin-St Jeor has two forms)
    activity_level     TEXT    CHECK (activity_level IS NULL OR activity_level IN
                                ('sedentary', 'light', 'moderate', 'very_active', 'extra_active')),  -- CR-2
    training_level     TEXT    CHECK (training_level IS NULL OR training_level IN
                                ('novice', 'intermediate', 'advanced')),                   -- CR-5
    deficit_level      TEXT    CHECK (deficit_level IS NULL OR deficit_level IN
                                ('small', 'moderate', 'large')),                           -- CR-3 optional
    intake_kcal        INTEGER CHECK (intake_kcal IS NULL OR intake_kcal > 0),             -- CR-3 optional
    UNIQUE (snapshot_id, user_id)  -- lets check-ins prove they belong to the same user
);

CREATE TRIGGER IF NOT EXISTS profile_snapshots_are_immutable
BEFORE UPDATE ON profile_snapshots
BEGIN
    SELECT RAISE(ABORT, 'profile snapshots are immutable: insert a new snapshot instead');
END;

-- FR-5: the ER relationship "CheckIn creates ProfileSnapshot" is 1:1, so snapshot_id is UNIQUE.
CREATE TABLE IF NOT EXISTS checkins (
    checkin_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    snapshot_id   INTEGER NOT NULL UNIQUE,
    checkin_date  TEXT    NOT NULL,                                    -- YYYY-MM-DD
    UNIQUE (user_id, checkin_date),                                    -- decision D-6 in docs/schema-notes.md
    FOREIGN KEY (snapshot_id, user_id)
        REFERENCES profile_snapshots (snapshot_id, user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exercises (
    exercise_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    muscle_group  TEXT NOT NULL
);

-- FR-6 and optional load entry: sets, reps and weight_used are nullable on purpose.
CREATE TABLE IF NOT EXISTS workout_logs (
    workout_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    checkin_id   INTEGER NOT NULL REFERENCES checkins(checkin_id) ON DELETE CASCADE,
    exercise_id  INTEGER NOT NULL REFERENCES exercises(exercise_id),
    session_day  TEXT    CHECK (session_day IS NULL OR session_day IN ('mon','tue','wed','thu','fri','sat','sun')),  -- decision D-2: the planned day this log belongs to
    sets         INTEGER CHECK (sets IS NULL OR sets > 0),
    reps         INTEGER CHECK (reps IS NULL OR reps > 0),
    weight_used  REAL    CHECK (weight_used IS NULL OR weight_used >= 0)
);

CREATE TABLE IF NOT EXISTS nutrition_logs (
    nutrition_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    checkin_id          INTEGER NOT NULL UNIQUE REFERENCES checkins(checkin_id) ON DELETE CASCADE,
    protein_target_met  INTEGER CHECK (protein_target_met IS NULL OR protein_target_met IN (0, 1)),
    notes               TEXT
);

CREATE TABLE IF NOT EXISTS sleep_logs (
    sleep_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    checkin_id  INTEGER NOT NULL UNIQUE REFERENCES checkins(checkin_id) ON DELETE CASCADE,
    bed_time    TEXT,                                                  -- HH:MM
    wake_time   TEXT                                                   -- HH:MM
);

-- FR-9, FR-12: computed by the trend engine, never typed in by users.
CREATE TABLE IF NOT EXISTS metrics (
    metric_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    metric_type  TEXT    NOT NULL,
    value        REAL    NOT NULL,
    computed_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS evidence_rules (
    rule_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    description  TEXT NOT NULL,
    citation     TEXT NOT NULL,
    version      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    generated_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    content            TEXT    NOT NULL,
    -- Decision D-3: who wrote it. 'rules' = the rule engine (or the rules fallback), 'llm' = the AI layer.
    source             TEXT    NOT NULL DEFAULT 'rules' CHECK (source IN ('rules', 'llm')),
    -- NULL for the weekly suggestion; the user's question when this row answers a free question (Ask screen).
    question           TEXT
);

-- FR-14, NFR-7: traceability. Link tables resolve the two many-to-many relationships in the ER diagram.
CREATE TABLE IF NOT EXISTS recommendation_metrics (
    recommendation_id  INTEGER NOT NULL REFERENCES recommendations(recommendation_id) ON DELETE CASCADE,
    metric_id          INTEGER NOT NULL REFERENCES metrics(metric_id) ON DELETE CASCADE,
    PRIMARY KEY (recommendation_id, metric_id)
);

CREATE TABLE IF NOT EXISTS recommendation_rules (
    recommendation_id  INTEGER NOT NULL REFERENCES recommendations(recommendation_id) ON DELETE CASCADE,
    rule_id            INTEGER NOT NULL REFERENCES evidence_rules(rule_id),
    PRIMARY KEY (recommendation_id, rule_id)
);

CREATE TABLE IF NOT EXISTS personas (
    persona_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL UNIQUE,
    config_description  TEXT
);

CREATE TABLE IF NOT EXISTS simulation_runs (
    run_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    persona_id         INTEGER NOT NULL REFERENCES personas(persona_id) ON DELETE CASCADE,
    recommendation_id  INTEGER NOT NULL REFERENCES recommendations(recommendation_id) ON DELETE CASCADE,
    timepoint_label    TEXT    NOT NULL                                -- e.g. 'week_1', 'week_6', 'week_12'
);

CREATE INDEX IF NOT EXISTS idx_snapshots_user_time ON profile_snapshots (user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_workouts_checkin    ON workout_logs (checkin_id);
CREATE INDEX IF NOT EXISTS idx_metrics_user_type   ON metrics (user_id, metric_type, computed_at);
CREATE INDEX IF NOT EXISTS idx_recs_user_time      ON recommendations (user_id, generated_at);
CREATE INDEX IF NOT EXISTS idx_runs_persona        ON simulation_runs (persona_id, timepoint_label);
