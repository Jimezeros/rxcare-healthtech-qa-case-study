DROP VIEW IF EXISTS prescription_quality_checks;

CREATE VIEW prescription_quality_checks AS
SELECT 'NULL_DOSAGE' AS check_name, COUNT(*) AS finding_count
FROM prescriptions
WHERE dosage_instruction IS NULL
UNION ALL
SELECT 'EMPTY_DOSAGE', COUNT(*)
FROM prescriptions
WHERE dosage_instruction = ''
UNION ALL
SELECT 'WHITESPACE_ONLY_DOSAGE', COUNT(*)
FROM prescriptions
WHERE dosage_instruction IS NOT NULL
  AND length(dosage_instruction) > 0
  AND length(
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
  ) = 0
UNION ALL
SELECT 'DUPLICATE_RECORD_ID_GROUPS', COUNT(*)
FROM (
    SELECT record_id
    FROM prescriptions
    GROUP BY record_id
    HAVING COUNT(*) > 1
);

DROP VIEW IF EXISTS audit_outcome_summary;

CREATE VIEW audit_outcome_summary AS
SELECT outcome, COUNT(*) AS event_count
FROM validation_events
GROUP BY outcome;
