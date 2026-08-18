# Evidence Publication Policy

Execution evidence may be published only when it corresponds to genuine
portfolio work against an approved, testable target. Source code, designed test
cases, and executed evidence are different artifact types and must never be
presented as interchangeable.

## Evidence-status vocabulary

- **PASS** means the stated case was executed in the stated environment and all
  recorded assertions passed.
- **FAIL** means the case was executed and at least one assertion failed.
- **BLOCKED — NOT EXECUTED** means an environmental or procedural constraint
  prevented execution. It is not a failure of the product and not PASS evidence.
- **NOT EXECUTED** means a case exists by design but has no execution result.
- **NOT REPRODUCED** may be used only when the relevant risk was actually tested
  in the stated execution mode and the suspected behaviour was not observed.

An implementation claim such as “a browser UI exists” describes the source
tree. It does not prove that the UI was served over TCP, rendered in a browser,
or exercised through visible user interaction.

## Publication checklist

Before committing a screenshot, video, export, database extract, or log:

1. Confirm that every displayed or serialized record is procedurally synthetic;
   do not derive fixtures from real patient, customer, employer, or client data.
2. Confirm that visible identifiers use an unmistakable synthetic convention,
   such as the `SYN-` prefix.
3. Capture only the application viewport needed to prove the result. Exclude or
   crop browser tabs, bookmarks, address bars with private URLs, desktop files,
   notifications, email addresses, account identifiers, avatars, and unrelated
   applications.
4. Review the image itself after capture. Cropping before capture is preferred;
   redaction is a fallback and must be irreversible in the published artifact.
5. Record the related Jira key, expected result, actual result, application
   version, execution mode, operating system/browser when relevant, and UTC
   capture time.
6. Ensure the expected and actual results are observable without exposing
   sensitive input values.
7. State whether the evidence came from an in-process handler, a genuine
   loopback TCP request, an automated browser, or a manual browser session.
8. Regenerate the SHA-256 manifest after adding approved evidence files.
9. Do not present a designed test as executed evidence.
10. Do not present a candidate or simulated defect as a confirmed application
    failure.

## Current evidence state

### Immutable v0.1.0 historical baseline

Run [`20260817T185026Z-v0.1.0`](evidence/execution/20260817T185026Z-v0.1.0/)
is the canonical v0.1.0 baseline. It contains synthetic request/response
records, assertions, sanitized audit rows, SQL finding counts, automated test
output, JUnit XML, runtime metadata, a source fingerprint, and a SHA-256
manifest. It remains immutable even after later versions are implemented.

That run executed the HTTP handler contract in-process. It did not execute a
live TCP listener or browser session, and it does not claim UI evidence.

### v0.2.0 implementation and verification

Version v0.2.0 includes a self-contained local browser UI and a loopback
evidence harness. The current automated regression suite passes **21/21** tests.
The final in-process API bundle is
[`20260817T212310Z-v0.2.0`](evidence/execution/20260817T212310Z-v0.2.0/).
It passed 5/5 API-contract cases and 21/21 automated tests. It remains evidence
of its narrower handler/service/database scope only and does not claim live
browser execution.

Run
[`20260817T212440Z-ui-loopback-v0.2.0`](evidence/execution/20260817T212440Z-ui-loopback-v0.2.0/)
records the attempted live-loopback stage as **BLOCKED — NOT EXECUTED**. The
restricted sandbox denied binding an ephemeral `127.0.0.1` port. Consequently,
no live health request, UI request, UI-TC-01 through UI-TC-04 workflow, browser
JavaScript interaction, or screenshot was executed in that run. Its metadata
and report must not be replaced with a PASS claim.

A new timestamped run must be created on an environment that permits loopback
TCP before live-network or browser execution is described as completed.
