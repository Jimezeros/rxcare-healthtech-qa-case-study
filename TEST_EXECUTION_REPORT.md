# RxCare v0.2.0 — Current execution status

## Automated and API/handler results

- Automated suite: **21/21 Passed**
- API-contract cases: **5/5 Passed** through the in-process HTTP handler
- RXQA-10: **Not reproduced in API/handler tests**
- Final API evidence run: **`20260817T212310Z-v0.2.0` — PASS**

- [automated human-readable output](evidence/execution/20260817T212310Z-v0.2.0/automated_test_output.txt)
- [JUnit XML](evidence/execution/20260817T212310Z-v0.2.0/junit.xml)
- [complete API evidence directory](evidence/execution/20260817T212310Z-v0.2.0/)

## Browser UI and live-loopback status

The v0.2.0 single-page UI is implemented, including accepted/rejected result
display, canonical-record verification, privacy-safe audit display, and the
accessible `Dosage is required` field error.

**Live loopback/browser execution: BLOCKED — NOT EXECUTED.**

The restricted sprint environment denied binding the required `127.0.0.1`
listener. Consequently:

- no UI-TC case is marked Passed;
- no browser JavaScript execution or DOM result is claimed;
- no UI screenshot is claimed;
- no live-port health or regression result is claimed; and
- RXQA-10 has no browser UI determination.

The blocked attempt is documented in the
[v0.2.0 loopback execution report](evidence/execution/20260817T212440Z-ui-loopback-v0.2.0/TEST_EXECUTION_REPORT.md)
and its [run metadata](evidence/execution/20260817T212440Z-ui-loopback-v0.2.0/run_metadata.json).
The normal-workstation retry procedure remains in [RUNBOOK_GR.md](RUNBOOK_GR.md).

## Historical v0.1.0 evidence

The verified v0.1.0 baseline is preserved separately:
[`20260817T185026Z-v0.1.0`](evidence/execution/20260817T185026Z-v0.1.0/).
That historical run recorded 5/5 API-contract cases, 16/16 automated tests,
zero canonical-data findings across its four implemented SQL checks, and no
live UI execution. It is not presented as evidence for the later v0.2.0 UI.
