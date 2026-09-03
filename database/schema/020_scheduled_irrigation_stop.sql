-- Persist planned irrigation duration so the backend can stop irrigation after restarts.
SET @column_exists = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'irrigation_record'
    AND column_name = 'planned_duration_minutes'
);
SET @statement = IF(
  @column_exists = 0,
  'ALTER TABLE irrigation_record ADD COLUMN planned_duration_minutes INT NULL AFTER executed_at',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;

SET @column_exists = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'irrigation_record'
    AND column_name = 'scheduled_stop_at'
);
SET @statement = IF(
  @column_exists = 0,
  'ALTER TABLE irrigation_record ADD COLUMN scheduled_stop_at DATETIME(6) NULL AFTER planned_duration_minutes',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;

SET @index_exists = (
  SELECT COUNT(*) FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = 'irrigation_record'
    AND index_name = 'idx_irrigation_scheduled_stop'
);
SET @statement = IF(
  @index_exists = 0,
  'ALTER TABLE irrigation_record ADD KEY idx_irrigation_scheduled_stop (scheduled_stop_at, status)',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;
