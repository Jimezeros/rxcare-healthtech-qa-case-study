# Execution evidence

The published v0.1.0 evidence baseline is [`20260817T185026Z-v0.1.0`](20260817T185026Z-v0.1.0/).

Each run is generated from a fresh temporary SQLite database and contains:

- UTC/runtime metadata and an explicit execution-mode statement;
- synthetic API request and response records;
- assertion results and canonical-storage checks;
- sanitized audit-event exports;
- SQL quality-check results;
- human-readable automated test output;
- JUnit XML;
- a SHA-256 manifest.

Evidence directories are immutable records. If code or test scope changes, a new timestamped run should be created instead of editing an older run.

