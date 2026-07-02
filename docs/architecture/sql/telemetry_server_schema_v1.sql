-- Telemetry Server Database Schema V1
-- Reference DDL for private telemetry-server (PostgreSQL 14+)

BEGIN;

CREATE TABLE telemetry_sticks_cache (
    stick_id                VARCHAR(64) PRIMARY KEY,
    device_public_key_id    VARCHAR(64) NOT NULL,
    attestation_mode        VARCHAR(16) NOT NULL,
    status                  VARCHAR(16) NOT NULL,
    synced_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE telemetry_events_quarantine (
    event_id                UUID PRIMARY KEY,
    stick_id                VARCHAR(64) NOT NULL,
    machine_fingerprint     VARCHAR(128),
    quarantine_reason       VARCHAR(64) NOT NULL,
    payload_json            JSONB NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at              TIMESTAMPTZ
);

CREATE INDEX idx_quarantine_reason ON telemetry_events_quarantine(quarantine_reason);
CREATE INDEX idx_quarantine_expires ON telemetry_events_quarantine(expires_at);

CREATE TABLE telemetry_events_accepted (
    event_id                UUID PRIMARY KEY,
    stick_id                VARCHAR(64) NOT NULL,
    machine_fingerprint     VARCHAR(128),
    rescue_version          VARCHAR(32),
    build_id                VARCHAR(64),
    ingest_status           VARCHAR(32) NOT NULL DEFAULT 'accepted',
    payload_json            JSONB NOT NULL,
    diagnostics_forwarded   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_accepted_stick ON telemetry_events_accepted(stick_id, created_at DESC);

CREATE TABLE telemetry_forward_outbox (
    outbox_id               BIGSERIAL PRIMARY KEY,
    event_id                UUID NOT NULL REFERENCES telemetry_events_accepted(event_id) ON DELETE CASCADE,
    target                  VARCHAR(64) NOT NULL DEFAULT 'diagnostics',
    attempts                INT NOT NULL DEFAULT 0,
    last_error              TEXT,
    next_retry_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at            TIMESTAMPTZ
);

CREATE INDEX idx_outbox_pending ON telemetry_forward_outbox(next_retry_at) WHERE completed_at IS NULL;

CREATE TABLE telemetry_ingest_audit (
    audit_id                BIGSERIAL PRIMARY KEY,
    event_id                UUID,
    stick_id                VARCHAR(64),
    http_status             INT NOT NULL,
    response_status         VARCHAR(64) NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ingest_audit_created ON telemetry_ingest_audit(created_at DESC);

COMMIT;
