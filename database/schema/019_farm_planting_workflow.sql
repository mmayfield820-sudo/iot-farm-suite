-- Farm-admin planned planting workflow. Actual planting date is written only
-- after all plot planting tasks are completed by farmers.
SET NAMES utf8mb4;

ALTER TABLE farm
  ADD COLUMN planned_planting_date DATE NULL COMMENT 'Farm-wide planned planting date',
  ADD COLUMN planting_template_version_id BIGINT NULL COMMENT 'Template selected for the planned planting';

ALTER TABLE farm
  ADD CONSTRAINT fk_farm_planting_template
  FOREIGN KEY (planting_template_version_id) REFERENCES crop_template_version(template_version_id);

ALTER TABLE management_task DROP CHECK chk_task_source;
ALTER TABLE management_task
  ADD CONSTRAINT chk_task_source CHECK (source IN ('template', 'ad_hoc', 'planting'));
