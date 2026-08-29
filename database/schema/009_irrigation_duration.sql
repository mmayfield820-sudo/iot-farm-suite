-- Persist the planned duration of an irrigation-on command.
-- Actual duration is derived by pairing a successful on command with the next successful off command.

SET @planned_duration_exists = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'irrigation_record'
    AND column_name = 'planned_duration_minutes'
);
SET @statement = IF(
  @planned_duration_exists = 0,
  'ALTER TABLE irrigation_record ADD COLUMN planned_duration_minutes INT NULL AFTER operator_id',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;
