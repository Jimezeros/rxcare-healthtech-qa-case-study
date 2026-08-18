# RxCare v0.2.0 — Οδηγός εκτέλεσης

Ο οδηγός αυτός εξηγεί πώς ο Δημήτρης μπορεί να αναπαράγει το πρώτο λειτουργικό τμήμα του RxCare σε υπολογιστή με Python 3.9 ή νεότερη έκδοση.

## 1. Τι εκτελείται

Το prototype διαθέτει τοπική web οθόνη, δέχεται συνθετικές εγγραφές φαρμακευτικής αγωγής, ελέγχει αν υπάρχει ουσιαστική οδηγία δοσολογίας, αποθηκεύει μόνο τις έγκυρες εγγραφές σε SQLite και δημιουργεί ελαχιστοποιημένα audit events.

Δεν απαιτεί εγκατάσταση εξωτερικού πακέτου.

## 2. Έλεγχος της έκδοσης Python

Από τον κεντρικό φάκελο του repository:

```bash
python3 --version
```

## 3. Εκτέλεση της αυτοματοποιημένης σουίτας

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Το αναμενόμενο αποτέλεσμα για την έκδοση `0.2.0` είναι `Ran 21 tests` και `OK`.

## 4. Δημιουργία νέου evidence run

```bash
PYTHONPATH=src python3 scripts/capture_execution_evidence.py
```

Η εντολή δημιουργεί νέο χρονοσημασμένο φάκελο μέσα στο `evidence/execution/`, χρησιμοποιεί φρέσκια προσωρινή SQLite βάση, εκτελεί τα API-contract cases και τα automated tests, εξάγει sanitized αποτελέσματα και δημιουργεί SHA-256 manifest.

## 5. Εκκίνηση του τοπικού HTTP listener

```bash
PYTHONPATH=src python3 -m rxcare --database runtime/rxcare.db
```

Αναμενόμενο μήνυμα:

```text
RxCare 0.2.0 listening on http://127.0.0.1:8000
```

Η εντολή παραμένει ενεργή μέχρι να πατηθεί `Ctrl+C`.

## 6. Άνοιγμα της τοπικής οθόνης

Σε browser ανοίξτε:

```text
http://127.0.0.1:8000/
```

Η σελίδα πρέπει να εμφανίζει `Prototype v0.2.0`, την προειδοποίηση `Synthetic data only`, τη φόρμα και τα τρία panels αποτελεσμάτων. Δεν υπάρχει login στην έκδοση αυτή· authentication/RBAC δεν ελέγχεται και δεν πρέπει να παρουσιαστεί ως υλοποιημένο.

## 7. Απλό health check

Σε δεύτερο Terminal:

```bash
curl -i http://127.0.0.1:8000/health
```

Αναμένεται HTTP `200` και `"status": "ok"`.

## 8. Απόρριψη κενού dosage μέσω API

```bash
curl -i \
  -H 'Content-Type: application/json' \
  -d '{"record_id":"SYN-LOCAL-001","patient_ref":"SYN-PAT-001","medication_name":"Synthetic Medicine","dosage_instruction":""}' \
  http://127.0.0.1:8000/api/v1/prescriptions
```

Αναμένεται HTTP `422`, reason code `DOSAGE_REQUIRED` και μήνυμα `Dosage is required`.

## 9. Αποδοχή έγκυρου dosage μέσω API

```bash
curl -i \
  -H 'Content-Type: application/json' \
  -d '{"record_id":"SYN-LOCAL-002","patient_ref":"SYN-PAT-002","medication_name":"Synthetic Medicine","dosage_instruction":"Take one unit once daily"}' \
  http://127.0.0.1:8000/api/v1/prescriptions
```

Αναμένεται HTTP `201` και `"status": "ACCEPTED"`.

## 10. Έλεγχος αποθήκευσης και audit

```bash
curl -i http://127.0.0.1:8000/api/v1/prescriptions/SYN-LOCAL-002
curl -i 'http://127.0.0.1:8000/api/v1/audit-events?record_id=SYN-LOCAL-002'
curl -i http://127.0.0.1:8000/api/v1/quality-checks
```

Το audit response δεν πρέπει να περιέχει patient reference, medication name ή dosage free text.

## 11. UI execution profile για RXQA-6 έως RXQA-9

Χρησιμοποιήστε φρέσκια βάση και τα σταθερά συνθετικά δεδομένα του [MANUAL_TEST_CASES_RXQA-5.md](MANUAL_TEST_CASES_RXQA-5.md). Υποβάλετε κάθε case ακριβώς μία φορά:

1. `RXQA-6 / TC-01`: κενό dosage — αναμένεται `REJECTED · HTTP 422`, inline `Dosage is required`, `NOT_FOUND` canonical αποτέλεσμα και ένα `REJECTED` audit event.
2. `RXQA-7 / TC-02`: ακριβώς τρία ASCII spaces — τα ίδια αποτελέσματα. Το `window.__rxcareEvidence` πρέπει να δείχνει `dosage_length: 3` και code points `[32, 32, 32]` χωρίς να αποθηκεύει το dosage text.
3. `RXQA-8 / TC-03`: πλήρες dosage — αναμένεται `ACCEPTED · HTTP 201`, ένα canonical record με ακριβώς το υποβληθέν dosage και ένα `ACCEPTED` audit event.
4. `RXQA-9 / TC-04`: κενό dosage — αναμένεται ένα audit event μόνο με τα εγκεκριμένα audit fields και χωρίς patient reference, medication ή dosage text.

Μετά τα τέσσερα cases, το αναμενόμενο συνολικό αποτέλεσμα είναι μία canonical εγγραφή και τέσσερα audit events: τρία `REJECTED` και ένα `ACCEPTED`. Όλα τα SQL quality-check findings πρέπει να είναι μηδέν.

## 12. Evidence και privacy review

- καταγράψτε UTC ώρα, έκδοση, source hash, Python/OS/browser και το ακριβές localhost URL·
- αποθηκεύστε μόνο application-viewport screenshots, χωρίς tabs, address bar, avatar, email, desktop ή ιδιωτικά URLs·
- χρησιμοποιήστε αποκλειστικά σταθερά `SYN-` identifiers και `Synthetic Medicine A/B/C/D`·
- για τα τρία spaces κρατήστε length/code-points evidence, επειδή ένα screenshot δεν αποδεικνύει αόρατους χαρακτήρες·
- δημιουργήστε SHA-256 manifest τελευταίο, αφού ολοκληρωθούν όλα τα αρχεία.

## 13. Περιορισμός της συγκεκριμένης εκτέλεσης

Στο περιορισμένο sprint environment η δημιουργία listener στο `127.0.0.1` επέστρεψε `PermissionError: [Errno 1] Operation not permitted`. Για αυτό τα browser cases δεν χαρακτηρίζονται Passed στην τρέχουσα evidence run. Αυτό είναι περιβαλλοντικός περιορισμός και όχι παρατηρημένο product defect.

Η εντολή για την ελεγχόμενη loopback εκτέλεση είναι:

```bash
PYTHONPATH=src python3 scripts/capture_ui_execution_evidence.py
```

Στο συγκεκριμένο περιβάλλον η εντολή δημιουργεί σκόπιμα ένα `BLOCKED — NOT EXECUTED` evidence bundle και τερματίζει χωρίς να κατασκευάζει ψευδές PASS. Σε υπολογιστή που επιτρέπει local listener, η ίδια εντολή εκτελεί τις τέσσερις HTTP ακολουθίες, τους SQL ελέγχους και τη regression suite. Η πραγματική χειροκίνητη εκτέλεση σε browser και τα privacy-reviewed screenshots παραμένουν ξεχωριστό βήμα.

## 14. Τι δεν αποδεικνύει αυτή η εκτέλεση

Η τοπική επιτυχία δεν αποτελεί απόδειξη για production deployment, κλινική ασφάλεια, κανονιστική συμμόρφωση, κυβερνοασφάλεια ή ολοκληρωμένο HealthTech προϊόν. Αποδεικνύει έναν συγκεκριμένο, αναπαραγώγιμο validation κύκλο με συνθετικά δεδομένα.
