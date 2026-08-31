-- Phase 2 requirement 4-6: the farmer's handling decision and note for a reminder.
ALTER TABLE plan_adjustment_reminder
  ADD COLUMN disposition_action VARCHAR(30) NULL AFTER reminder_status,
  ADD COLUMN disposition_note VARCHAR(1000) NULL AFTER disposition_action,
  ADD COLUMN disposed_by BIGINT NULL AFTER disposition_note,
  ADD COLUMN disposed_at DATETIME(6) NULL AFTER disposed_by,
  DROP CHECK chk_plan_adjustment_reminder_status,
  ADD CONSTRAINT fk_plan_adjustment_reminder_disposed_by
    FOREIGN KEY (disposed_by) REFERENCES users (user_id),
  ADD CONSTRAINT chk_plan_adjustment_reminder_status CHECK (
    reminder_status IN ('active', 'handled', 'recovered')
  ),
  ADD CONSTRAINT chk_plan_adjustment_reminder_disposition CHECK (
    disposition_action IS NULL OR disposition_action IN (
      'adjust_as_suggested', 'keep_original_plan', 'handled'
    )
  );
