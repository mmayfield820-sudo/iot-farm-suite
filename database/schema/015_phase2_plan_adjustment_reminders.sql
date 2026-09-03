-- Phase 2 requirement 4-5: plan-adjustment reminders and their affected task snapshots.
CREATE TABLE plan_adjustment_reminder (
  reminder_id BIGINT NOT NULL AUTO_INCREMENT,
  plot_id BIGINT NOT NULL,
  reminder_type VARCHAR(30) NOT NULL,
  dedupe_key VARCHAR(100) NOT NULL,
  reminder_description VARCHAR(1000) NOT NULL,
  triggered_at DATETIME(6) NOT NULL,
  reminder_status VARCHAR(20) NOT NULL DEFAULT 'active',
  recovered_at DATETIME(6) NULL,
  PRIMARY KEY (reminder_id),
  UNIQUE KEY uq_plan_adjustment_reminder_dedupe (dedupe_key),
  KEY idx_plan_adjustment_reminder_plot_status (plot_id, reminder_status, triggered_at),
  CONSTRAINT fk_plan_adjustment_reminder_plot FOREIGN KEY (plot_id) REFERENCES plot (plot_id),
  CONSTRAINT chk_plan_adjustment_reminder_type CHECK (
    reminder_type IN ('low_moisture', 'continuous_rain', 'device_offline')
  ),
  CONSTRAINT chk_plan_adjustment_reminder_status CHECK (
    reminder_status IN ('active', 'recovered')
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE plan_adjustment_reminder_task (
  reminder_id BIGINT NOT NULL,
  task_id BIGINT NOT NULL,
  task_title VARCHAR(150) NOT NULL,
  task_type VARCHAR(50) NOT NULL,
  scheduled_date DATE NOT NULL,
  PRIMARY KEY (reminder_id, task_id),
  CONSTRAINT fk_plan_adjustment_reminder_task_reminder
    FOREIGN KEY (reminder_id) REFERENCES plan_adjustment_reminder (reminder_id),
  CONSTRAINT fk_plan_adjustment_reminder_task_task
    FOREIGN KEY (task_id) REFERENCES management_task (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
