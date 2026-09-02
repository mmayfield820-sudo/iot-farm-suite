-- Distinguish farm-admin supplements for work completed in undispatched historical stages.
SET NAMES utf8mb4;

ALTER TABLE management_task DROP CHECK chk_task_source;
ALTER TABLE management_task
  MODIFY COLUMN source VARCHAR(30) NOT NULL DEFAULT 'template',
  ADD CONSTRAINT chk_task_source
  CHECK (source IN ('template', 'ad_hoc', 'planting', 'temporary', 'historical_supplement'));
