# FAQ Notifications (EN)

## Why do I see a dashboard event but no email?

Dashboard visibility and email delivery are evaluated separately. An event can be persisted and visible while SMTP is not configured or the delivery attempt failed.

## What does `not_configured` mean?

SMTP or recipient configuration is incomplete, so no real email send was possible.

## What does `failed` mean?

An actual send attempt happened, but SMTP/Auth/TLS/network delivery failed. Details are stored in redacted form in `email_error`.

If the provider blocks delivery with `554 5.7.0` because of a sending limit, the classification is `notification.email.provider_limit_exceeded`. In that case the dashboard stays green/visible, but the email path remains yellow and `next_action=check_smtp_provider_limit_or_wait`.

## Where is the event history stored?

- locally in the workspace:
  - `docs/evidence/runtime-results/notifications/notification_events.jsonl`
  - `docs/evidence/runtime-results/notifications/notification_latest_summary.json`
- in the productive `/opt/setuphelfer` runtime:
  - `/var/lib/setuphelfer/notifications/notification_events.jsonl`
  - `/var/lib/setuphelfer/notifications/notification_latest_summary.json`

## How do I create a test event?

- Dashboard test: `POST /api/dev-dashboard/notifications/test-dashboard`
- Test email: `POST /api/dev-dashboard/notifications/test-email`

## Why was the Rescue ISO failure previously not delivered as a notification?

Because the old implementation only covered backup-related email logic and had no general dev-dashboard notification stack for rescue failures.
