-- Beta Registration Database Schema V1
-- Reference DDL for private beta-registration-server (PostgreSQL 14+)
-- Public repo: structure only — no production data

BEGIN;

CREATE TYPE stick_type_enum AS ENUM ('team_provisioned', 'registered_iso');
CREATE TYPE stick_status_enum AS ENUM ('provisioned', 'active', 'revoked', 'expired');
CREATE TYPE attestation_mode_enum AS ENUM ('hmac', 'signature');
CREATE TYPE account_status_enum AS ENUM ('active', 'restricted', 'revoked');
CREATE TYPE agreement_status_enum AS ENUM ('missing', 'pending', 'valid', 'expired', 'revoked');
CREATE TYPE approval_status_enum AS ENUM ('unknown', 'pending', 'approved', 'blocked', 'revoked');

CREATE TABLE beta_accounts (
    account_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_hash          VARCHAR(64) NOT NULL UNIQUE,
    email_verified_at   TIMESTAMPTZ,
    mfa_enabled         BOOLEAN NOT NULL DEFAULT FALSE,
    status              account_status_enum NOT NULL DEFAULT 'active',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE beta_agreements (
    agreement_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id          UUID NOT NULL REFERENCES beta_accounts(account_id) ON DELETE CASCADE,
    version             VARCHAR(32) NOT NULL,
    status              agreement_status_enum NOT NULL DEFAULT 'missing',
    telemetry_consent   BOOLEAN NOT NULL DEFAULT FALSE,
    signed_at           TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (account_id, version)
);

CREATE TABLE beta_stick_registry (
    stick_id                VARCHAR(64) PRIMARY KEY,
    stick_type              stick_type_enum NOT NULL,
    account_id              UUID REFERENCES beta_accounts(account_id) ON DELETE SET NULL,
    device_public_key_id    VARCHAR(64) NOT NULL,
    attestation_mode        attestation_mode_enum NOT NULL,
    status                  stick_status_enum NOT NULL DEFAULT 'provisioned',
    team_batch_id           VARCHAR(64),
    iso_build_id            VARCHAR(64),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at              TIMESTAMPTZ
);

CREATE INDEX idx_stick_registry_status ON beta_stick_registry(status);
CREATE INDEX idx_stick_registry_account ON beta_stick_registry(account_id);

CREATE TABLE beta_machines (
    machine_fingerprint     VARCHAR(128) PRIMARY KEY,
    account_id              UUID NOT NULL REFERENCES beta_accounts(account_id) ON DELETE CASCADE,
    stick_id                VARCHAR(64) REFERENCES beta_stick_registry(stick_id) ON DELETE SET NULL,
    approval_status         approval_status_enum NOT NULL DEFAULT 'unknown',
    first_seen_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_machines_pending ON beta_machines(approval_status) WHERE approval_status = 'pending';

CREATE TABLE beta_activation_tokens (
    token_hash              VARCHAR(64) PRIMARY KEY,
    account_id              UUID NOT NULL REFERENCES beta_accounts(account_id) ON DELETE CASCADE,
    iso_build_id            VARCHAR(64) NOT NULL,
    expires_at              TIMESTAMPTZ NOT NULL,
    consumed_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_activation_tokens_expires ON beta_activation_tokens(expires_at);

CREATE TABLE machine_approval_audit (
    audit_id                BIGSERIAL PRIMARY KEY,
    machine_fingerprint     VARCHAR(128) NOT NULL,
    from_status             VARCHAR(32),
    to_status               VARCHAR(32) NOT NULL,
    operator_id             VARCHAR(64) NOT NULL,
    reason                  TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_approval_audit_fp ON machine_approval_audit(machine_fingerprint, created_at DESC);

COMMIT;
