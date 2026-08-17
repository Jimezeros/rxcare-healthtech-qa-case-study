PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS prescriptions (
    record_id TEXT PRIMARY KEY,
    patient_ref TEXT NOT NULL,
    medication_name TEXT NOT NULL,
    dosage_instruction TEXT NOT NULL
        CHECK (
            length(
                trim(
                    dosage_instruction,
                    char(9) || char(10) || char(11) || char(12) ||
                    char(13) || char(28) || char(29) || char(30) ||
                    char(31) || char(32) || char(133) || char(160) ||
                    char(5760) || char(8192) || char(8193) ||
                    char(8194) || char(8195) || char(8196) ||
                    char(8197) || char(8198) || char(8199) ||
                    char(8200) || char(8201) || char(8202) ||
                    char(8232) || char(8233) || char(8239) ||
                    char(8287) || char(12288)
                )
            ) > 0
        ),
    created_at_utc TEXT NOT NULL,
    app_version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS validation_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id TEXT UNIQUE NOT NULL,
    timestamp_utc TEXT NOT NULL,
    action TEXT NOT NULL
        CHECK (action = 'PRESCRIPTION_VALIDATION'),
    record_id TEXT NOT NULL,
    outcome TEXT NOT NULL
        CHECK (outcome IN ('ACCEPTED', 'REJECTED')),
    reason_code TEXT,
    app_version TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_validation_events_record_id
    ON validation_events(record_id);
