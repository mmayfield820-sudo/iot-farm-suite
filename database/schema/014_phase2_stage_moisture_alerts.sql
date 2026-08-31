-- Phase 2: allow alerts when the current production stage's moisture upper bound is exceeded.
ALTER TABLE alert
  DROP CHECK chk_alert_type,
  ADD CONSTRAINT chk_alert_type CHECK (
    alert_type IN (
      'low_moisture', 'high_moisture', 'device_offline',
      'device_fault', 'irrigation_failed'
    )
  );
