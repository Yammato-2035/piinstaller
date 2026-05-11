# Recovery Activation Controlled Execute

Recovery Activation Controlled Execute enables the first narrowly scoped activation writes inside `target_path`, guarded by session+token+TTL and strict step-level validation.

## Guarantees

- single-use activation sessions
- session-bound selected steps only
- fail-fast execution with per-step result codes
- containment-safe writes below `target_path`
- no host-level service/user/network mutation

## Security specifics

- SSH key step validates allowed public key types and blocks private/multiline/suspicious payloads
- password login and root login are prepared as disabled in target config only
- backend bind defaults to localhost; LAN bind (`0.0.0.0`) requires explicit confirmation and emits warning code

## API contract

- Endpoint: `POST /api/recovery/activation/execute`
- New fields: `ssh_public_key`, `allow_lan_backend_bind`
- Stable result envelope: `code`, `activation_session_id`, `steps[]`, `warnings[]`, `errors[]`
