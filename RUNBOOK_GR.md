# RxCare v0.1.0 — Οδηγός εκτέλεσης

Ο οδηγός αυτός εξηγεί πώς ο Δημήτρης μπορεί να αναπαράγει το πρώτο λειτουργικό τμήμα του RxCare σε υπολογιστή με Python 3.9 ή νεότερη έκδοση.

## 1. Τι εκτελείται

Το prototype δέχεται συνθετικές εγγραφές φαρμακευτικής αγωγής, ελέγχει αν υπάρχει ουσιαστική οδηγία δοσολογίας, αποθηκεύει μόνο τις έγκυρες εγγραφές σε SQLite και δημιουργεί ελαχιστοποιημένα audit events.

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

Το αναμενόμενο αποτέλεσμα για την έκδοση `0.1.0` είναι `Ran 16 tests` και `OK`.

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
RxCare 0.1.0 listening on http://127.0.0.1:8000
```

Η εντολή παραμένει ενεργή μέχρι να πατηθεί `Ctrl+C`.

## 6. Απλό health check

Σε δεύτερο Terminal:

```bash
curl -i http://127.0.0.1:8000/health
```

Αναμένεται HTTP `200` και `"status": "ok"`.

## 7. Απόρριψη κενού dosage

```bash
curl -i \
  -H 'Content-Type: application/json' \
  -d '{"record_id":"SYN-LOCAL-001","patient_ref":"SYN-PAT-001","medication_name":"Synthetic Medicine","dosage_instruction":""}' \
  http://127.0.0.1:8000/api/v1/prescriptions
```

Αναμένεται HTTP `422`, reason code `DOSAGE_REQUIRED` και μήνυμα `Dosage is required`.

## 8. Αποδοχή έγκυρου dosage

```bash
curl -i \
  -H 'Content-Type: application/json' \
  -d '{"record_id":"SYN-LOCAL-002","patient_ref":"SYN-PAT-002","medication_name":"Synthetic Medicine","dosage_instruction":"Take one unit once daily"}' \
  http://127.0.0.1:8000/api/v1/prescriptions
```

Αναμένεται HTTP `201` και `"status": "ACCEPTED"`.

## 9. Έλεγχος αποθήκευσης και audit

```bash
curl -i http://127.0.0.1:8000/api/v1/prescriptions/SYN-LOCAL-002
curl -i 'http://127.0.0.1:8000/api/v1/audit-events?record_id=SYN-LOCAL-002'
curl -i http://127.0.0.1:8000/api/v1/quality-checks
```

Το audit response δεν πρέπει να περιέχει patient reference, medication name ή dosage free text.

## 10. Τι δεν αποδεικνύει αυτή η εκτέλεση

Η τοπική επιτυχία δεν αποτελεί απόδειξη για production deployment, κλινική ασφάλεια, κανονιστική συμμόρφωση, κυβερνοασφάλεια ή ολοκληρωμένο HealthTech προϊόν. Αποδεικνύει έναν συγκεκριμένο, αναπαραγώγιμο validation κύκλο με συνθετικά δεδομένα.

