# Rescue Developer Agent Profile

Profile roots:
- Developer: `build/rescue/profiles/developer/`
- Public guard: `build/rescue/profiles/public/`

Validation: `backend/devserver_agent/rescue_profile.py`
Guard script: `scripts/check-dev-agent-rescue-profile-guard.sh`

Public rescue never auto-uploads. Developer edition sends only to local dev server in local_lab mode.
