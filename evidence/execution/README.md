# Execution evidence

This directory contains timestamped execution records. A run proves only the
scope and execution mode stated inside its own metadata and report.

## Status summary

### v0.1.0 historical baseline

The canonical v0.1.0 baseline is
[`20260817T185026Z-v0.1.0`](20260817T185026Z-v0.1.0/). It used a fresh temporary
SQLite database and exercised the HTTP handler in-process. Its synthetic API
cases, persistence checks, privacy-safe audit checks, SQL checks, automated
test results, source manifest, and checksums are genuine evidence for that
scope. It did not open a live TCP listener or execute a browser.

The earlier v0.1.0 directories are retained as historical development runs.
They are not rewritten or silently promoted when a later run becomes canonical.

### v0.2.0 in-process verification

The v0.2.0 source tree includes a self-contained local browser UI. Preliminary
local bundles created before the final source/test reconciliation are excluded
from the public release rather than silently promoted. Historical bundles are
never edited to carry a later test count or broader execution claim.

The current v0.2.0 automated regression suite passes **21/21** tests.

The canonical v0.2.0 in-process API bundle is
[`20260817T212310Z-v0.2.0`](20260817T212310Z-v0.2.0/). It passed 5/5 API cases
and 21/21 automated tests against the source fingerprint recorded in its
metadata. Its SHA-256 manifest verifies successfully. It does not claim a live
TCP listener or browser execution.

### v0.2.0 live-loopback attempt

Run
[`20260817T212440Z-ui-loopback-v0.2.0`](20260817T212440Z-ui-loopback-v0.2.0/)
is explicitly **BLOCKED — NOT EXECUTED**. The sandbox denied creation of the
required ephemeral `127.0.0.1` listener. No live HTTP request, UI workflow,
browser interaction, screenshot, SQL result, or new RXQA-10 determination is
claimed by that bundle.

The run is useful as auditable evidence of an environment constraint, not as a
product PASS or FAIL. The loopback harness is ready to create a new run on a
normal workstation:

```text
PYTHONPATH=src python3 scripts/capture_ui_execution_evidence.py
```

## Expected contents of a completed run

Depending on the execution mode, a completed evidence bundle may contain:

- UTC/runtime metadata and an explicit execution-mode statement;
- a source-tree SHA-256 fingerprint;
- synthetic HTTP request and response records;
- assertion results and canonical-storage checks;
- privacy-safe audit-event exports;
- pre/post SQLite counts and SQL quality-check results;
- human-readable automated test output and JUnit XML;
- approved viewport-only screenshots captured separately when a real browser
  was executed;
- a SHA-256 manifest generated after all approved files are present.

Absence of an artifact must be stated directly. A served HTML route is not the
same as a browser-rendered screenshot, and an in-process HTTP handler is not the
same as a live TCP listener.

## Immutability rule

Evidence directories are immutable historical records. If code, tests,
environment, execution mode, or screenshot scope changes, create a new
timestamped run. Never edit an older report to describe work that occurred
later. If screenshots are added to a new active run, perform the privacy review
first and generate the SHA-256 manifest last.
