# Synthetic Test Data Policy

Only fictional, procedurally created data may enter the RxCare prototype,
evidence bundles, screenshots, documentation, or repository history.

## Procedural synthetic-only boundary

The boundary applies before data reaches the application:

1. Create a test fixture specifically for the case; never copy, transform,
   mask, hash, or pseudonymize a real patient, prescription, customer, employer,
   or client record.
2. Use unmistakable identifiers beginning with `SYN-` for record and patient
   references.
3. Use obviously fictional medication names and non-clinical example
   instructions created solely for software testing.
4. Submit the fixture only to a fresh local test database.
5. Export only the minimum fields required to prove the expected result.
6. Delete the temporary database after the sanitized evidence export.

Redaction does not convert real data into approved test data. If the origin of
a value is uncertain, do not enter or publish it.

## Permitted examples

- identifiers such as `SYN-UI-TC-03` and `SYN-PAT-UI-03`;
- fictional medication records created solely for test design;
- synthetic roles, timestamps, audit events, and consent metadata;
- clearly labelled AI-output examples used as evaluation artifacts;
- runtime metadata that does not expose a username, home-directory path,
  account, credential, private URL, or unique personal device identifier.

The word “synthetic” describes origin, not clinical correctness. Fictional
dosage text in this repository is not medical advice and must not be reused for
care decisions.

## Prohibited content

- real or pseudonymized patient, prescription, pharmacy, or customer data;
- employer, client, project-platform, or production-system records;
- copied proprietary interfaces, datasets, prompts, or workflows;
- names or professional details of private individuals unless a separate,
  explicit publication purpose and consent have been established;
- personal email addresses, phone numbers, account identifiers, avatars,
  private URLs, browser profiles, or visible desktop filenames;
- credentials, tokens, keys, cookies, session values, or configuration secrets;
- absolute paths that expose a personal username or private directory layout.

## Screenshot and video safety

Browser evidence is permitted only after a separate privacy review:

- populate every visible form field with approved `SYN-` fixtures;
- capture the application viewport only;
- exclude browser tabs, bookmarks, profile icons, account menus, address bars
  containing private URLs, notifications, other applications, and the desktop;
- ensure canonical-record output contains only the approved synthetic fixture;
- ensure audit output contains only the approved privacy-safe fields and never
  patient reference, medication, or dosage text;
- record the application version, Jira/test-case key, browser/OS, and UTC time
  in a separate safe metadata file;
- inspect the final image at full resolution before publication;
- generate or refresh the evidence SHA-256 manifest only after the approved
  screenshot files are final.

## Review responsibility

Every dataset and visual artifact requires a final human privacy review before
publication. Automated scanning is a supporting control, not a substitute for
that review.
