-- A registered device may exist before an administrator binds it to a plot.
SET @is_nullable = (
  SELECT IS_NULLABLE = 'YES'
  FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'device' AND column_name = 'plot_id'
);
SET @sql = IF(@is_nullable = 0,
  'ALTER TABLE device MODIFY plot_id BIGINT NULL',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
