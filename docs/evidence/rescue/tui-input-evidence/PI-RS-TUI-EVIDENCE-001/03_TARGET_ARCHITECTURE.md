# Target architecture

Runtime-first evidence; bounded SETUP_LOGS wait; atomic `.partial` publish;
shutdown gate until persisted. See module `rescue_tui_input_diagnostic_persistence.py`.

Status model: `runtime_only` | `waiting_for_persistent_root` | `copying` | `verifying` |
`persisted` | `review_required` | `blocked` | `aborted`.

`passed` only outside finalizer after full persistence (diagnostic keeps `review_required`
for hypothesis work; persistence is a separate gate).
