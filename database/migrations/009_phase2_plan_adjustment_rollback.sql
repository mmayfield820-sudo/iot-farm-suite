ALTER TABLE alert
  DROP CHECK chk_alert_resolution_action,
  ADD CONSTRAINT chk_alert_resolution_action
    CHECK (resolution_action IS NULL OR resolution_action IN ('ADJUST', 'KEEP_PLAN', 'HANDLED', 'ROLLED_BACK'));
