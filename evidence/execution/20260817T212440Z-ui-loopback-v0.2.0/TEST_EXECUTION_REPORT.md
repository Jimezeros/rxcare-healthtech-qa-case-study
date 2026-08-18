# RxCare v0.2.0 — Phase 2 loopback execution report

## Result

**BLOCKED — NOT EXECUTED.**

- Run ID: `20260817T212440Z-ui-loopback-v0.2.0`
- UTC attempt time: `2026-08-17T21:24:40Z`
- Required transport: genuine TCP HTTP/1.1 on a loopback-only port
- Listener status: the execution environment denied the loopback bind
- Submitted records: none
- Browser/screenshots: not executed

No UI-TC case, health request, SQL result, regression result, or RXQA-10
determination is presented as executed by this run. This bundle exists to make
the environmental constraint auditable; it is not PASS evidence and must not
be substituted for a workstation loopback run.

## How to retry

From the repository root on a workstation that permits `127.0.0.1` listeners:

```text
PYTHONPATH=src python3 scripts/capture_ui_execution_evidence.py
```

The script will use an OS-assigned ephemeral port, a fresh temporary SQLite
database, synthetic data only, and will exit non-zero unless every network,
case, count, SQL, and regression assertion passes.
