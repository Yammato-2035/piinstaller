-- Diagnostics Hardware Database Schema V1
-- Reference DDL for private diagnostics-server (PostgreSQL 14+)

BEGIN;

CREATE TYPE review_status_enum AS ENUM ('pending', 'approved', 'rejected');

CREATE TABLE hardware_profiles (
    hardware_key            VARCHAR(64) PRIMARY KEY,
    trait_vector            JSONB NOT NULL,
    observation_count       INT NOT NULL DEFAULT 0,
    review_status           review_status_enum NOT NULL DEFAULT 'pending',
    last_observation_at     TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE hardware_observations (
    observation_id          BIGSERIAL PRIMARY KEY,
    event_id                UUID NOT NULL UNIQUE,
    hardware_key            VARCHAR(64) NOT NULL REFERENCES hardware_profiles(hardware_key) ON DELETE CASCADE,
    stick_id                VARCHAR(64) NOT NULL,
    rescue_version          VARCHAR(32),
    build_id                VARCHAR(64),
    assessment_summary      JSONB NOT NULL,
    review_required         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_observations_hw ON hardware_observations(hardware_key, created_at DESC);
CREATE INDEX idx_observations_review ON hardware_observations(review_required) WHERE review_required = TRUE;

CREATE TABLE hardware_review_queue (
    queue_id                BIGSERIAL PRIMARY KEY,
    observation_id          BIGINT NOT NULL REFERENCES hardware_observations(observation_id) ON DELETE CASCADE,
    status                  review_status_enum NOT NULL DEFAULT 'pending',
    assigned_operator_id    VARCHAR(64),
    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at             TIMESTAMPTZ
);

CREATE INDEX idx_review_queue_pending ON hardware_review_queue(status) WHERE status = 'pending';

CREATE TABLE learning_import_audit (
    audit_id                BIGSERIAL PRIMARY KEY,
    event_id                UUID,
    import_status           VARCHAR(32) NOT NULL,
    http_status             INT,
    error_detail            TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_learning_audit_created ON learning_import_audit(created_at DESC);

COMMIT;
