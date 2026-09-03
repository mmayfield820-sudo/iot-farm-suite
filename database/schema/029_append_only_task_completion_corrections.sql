-- Preserve the original completion and append corrections as new records.
SET NAMES utf8mb4;

ALTER TABLE management_task_completion
  DROP INDEX uq_task_completion_task,
  ADD COLUMN record_type VARCHAR(20) NOT NULL DEFAULT 'completion' AFTER irrigation_record_id,
  ADD COLUMN corrects_completion_id BIGINT NULL AFTER record_type,
  ADD KEY idx_task_completion_task_created (task_id, task_completion_id),
  ADD KEY idx_task_completion_corrects (corrects_completion_id),
  ADD CONSTRAINT chk_task_completion_record_type
    CHECK (record_type IN ('completion', 'correction')),
  ADD CONSTRAINT fk_task_completion_corrected_record
    FOREIGN KEY (corrects_completion_id) REFERENCES management_task_completion(task_completion_id);
