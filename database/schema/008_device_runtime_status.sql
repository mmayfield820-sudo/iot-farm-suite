-- Separate device communication state from collection/work state.
-- Safe to run repeatedly against an existing local database.

SET @work_status_exists = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'device' AND column_name = 'work_status'
);
SET @statement = IF(
  @work_status_exists = 0,
  "ALTER TABLE device ADD COLUMN work_status VARCHAR(20) NOT NULL DEFAULT 'stopped' AFTER status",
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;
