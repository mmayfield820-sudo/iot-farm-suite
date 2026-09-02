-- Support recurring orchard work within each annual growth-stage window.
SET NAMES utf8mb4;

SET @column_exists = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'management_task_template'
    AND column_name = 'repeat_days'
);
SET @statement = IF(
  @column_exists = 0,
  'ALTER TABLE management_task_template ADD COLUMN repeat_days INT NULL COMMENT ''Interval in days for a recurring task''',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;

SET @column_exists = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'management_task_template'
    AND column_name = 'repeat_until_stage_end'
);
SET @statement = IF(
  @column_exists = 0,
  'ALTER TABLE management_task_template ADD COLUMN repeat_until_stage_end TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''Expand occurrences through the end of the stage''',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;

SET @constraint_exists = (
  SELECT COUNT(*) FROM information_schema.table_constraints
  WHERE constraint_schema = DATABASE()
    AND table_name = 'management_task_template'
    AND constraint_name = 'chk_task_template_repeat_days'
);
SET @statement = IF(
  @constraint_exists = 0,
  'ALTER TABLE management_task_template ADD CONSTRAINT chk_task_template_repeat_days CHECK (repeat_days IS NULL OR repeat_days > 0)',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;

SET @constraint_exists = (
  SELECT COUNT(*) FROM information_schema.table_constraints
  WHERE constraint_schema = DATABASE()
    AND table_name = 'management_task_template'
    AND constraint_name = 'chk_task_template_repeat_rule'
);
SET @statement = IF(
  @constraint_exists = 0,
  'ALTER TABLE management_task_template ADD CONSTRAINT chk_task_template_repeat_rule CHECK (repeat_until_stage_end = 0 OR repeat_days IS NOT NULL)',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;

-- Inspections and field observations recur. One-off operations such as
-- fertilizing, thinning and cleanup keep their original single date.
UPDATE management_task_template AS task
JOIN growth_stage_template AS stage ON stage.stage_template_id = task.stage_template_id
JOIN crop_template_version AS version ON version.template_version_id = stage.template_version_id
SET task.repeat_days = CASE
      WHEN stage.stage_code = 'S1' AND task.task_type = 'inspection' AND task.offset_days = 28 THEN 14
      WHEN stage.stage_code = 'S2' AND task.task_type = 'inspection' AND task.offset_days = 0 THEN 14
      WHEN stage.stage_code = 'S2' AND task.task_type = 'irrigation' AND task.offset_days = 7 THEN 7
      WHEN stage.stage_code = 'S2' AND task.task_type = 'pruning' AND task.offset_days = 21 THEN 14
      WHEN stage.stage_code = 'S2' AND task.task_type = 'flower_management' AND task.track = 'young' THEN 7
      WHEN stage.stage_code = 'S3' AND task.task_type = 'inspection' AND task.offset_days = 0 THEN 7
      WHEN stage.stage_code = 'S3' AND task.task_type = 'flower_management' THEN 7
      WHEN stage.stage_code = 'S3' AND task.task_type = 'pest_control' THEN 7
      WHEN stage.stage_code = 'S4' AND task.task_type = 'pruning' THEN 14
      WHEN stage.stage_code = 'S4' AND task.task_type = 'pest_control' THEN 14
      WHEN stage.stage_code = 'S5' AND task.task_type = 'irrigation' THEN 7
      WHEN stage.stage_code = 'S5' AND task.task_type IN ('inspection', 'pruning') THEN 14
      WHEN stage.stage_code = 'S6' AND task.task_type IN ('pruning', 'inspection', 'irrigation') THEN 7
      WHEN stage.stage_code = 'S7' AND task.task_type = 'harvest' THEN 7
      ELSE task.repeat_days
    END
WHERE version.version_status = 'published'
  AND stage.stage_code IN ('S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7');

UPDATE management_task_template AS task
JOIN growth_stage_template AS stage ON stage.stage_template_id = task.stage_template_id
JOIN crop_template_version AS version ON version.template_version_id = stage.template_version_id
SET task.repeat_until_stage_end = 1
WHERE version.version_status = 'published'
  AND stage.stage_code IN ('S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7')
  AND task.repeat_days IS NOT NULL;

-- Correct result-bearing work that existed before track-specific templates.
UPDATE management_task_template AS task
JOIN growth_stage_template AS stage ON stage.stage_template_id = task.stage_template_id
JOIN crop_template_version AS version ON version.template_version_id = stage.template_version_id
SET task.track = 'fruiting'
WHERE version.version_status = 'published'
  AND task.track IS NULL
  AND (
    (stage.stage_code = 'S3' AND task.task_type = 'flower_management')
    OR (stage.stage_code = 'S4' AND task.task_type = 'fruit_management')
    OR (stage.stage_code = 'S6' AND task.task_type = 'inspection' AND task.offset_days = 14)
    OR (stage.stage_code = 'S7' AND task.task_type = 'harvest' AND task.offset_days = 0)
  );
