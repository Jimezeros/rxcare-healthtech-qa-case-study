# Evidence Publication Policy

Execution evidence may be published only when it corresponds to genuine portfolio work against an approved testable target.

Before committing a screenshot, video, export, or log:

1. Confirm that every displayed record is synthetic.
2. Hide email addresses, account identifiers, avatars, browser tabs, and private URLs.
3. Record the related Jira key, test environment, build/version, and capture date.
4. Confirm that expected and actual results are observable.
5. Do not present a designed test as executed evidence.
6. Do not present a candidate or simulated defect as a confirmed application failure.

## Current published execution evidence

Run `20260817T185026Z-v0.1.0` contains synthetic request/response records, assertions, sanitized audit rows, SQL finding counts, automated test output, JUnit XML, runtime metadata, and a SHA-256 manifest.

The run states its limitations directly: the HTTP handler contract was executed in-process, the live TCP listener was not executed in the restricted environment, and the Jira UI-oriented test cases remain Not Executed.
