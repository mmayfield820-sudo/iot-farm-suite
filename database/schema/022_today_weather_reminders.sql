-- Final reminder scope: today's read-only weather notices that affect today's farm work.
SET NAMES utf8mb4;

ALTER TABLE plan_adjustment_reminder
  DROP CHECK chk_plan_adjustment_reminder_type,
  ADD CONSTRAINT chk_plan_adjustment_reminder_type CHECK (
    reminder_type IN (
      'low_moisture',
      'device_offline',
      'continuous_rain',
      'high_rain_probability',
      'high_temperature',
      'frost_risk',
      'strong_wind'
    )
  );
