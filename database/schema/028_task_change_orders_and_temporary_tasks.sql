-- Distinguish farm-admin temporary work from farmer ad-hoc completion records.
SET NAMES utf8mb4;

ALTER TABLE management_task DROP CHECK chk_task_source;
ALTER TABLE management_task
  ADD CONSTRAINT chk_task_source
  CHECK (source IN ('template', 'ad_hoc', 'planting', 'temporary'));
