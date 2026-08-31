-- Stage 1: unified plan and farm-work task storage.
SET NAMES utf8mb4;

CREATE TABLE farm_task (
  task_id BIGINT NOT NULL AUTO_INCREMENT,
  plot_id BIGINT NOT NULL,
  template_id BIGINT NULL,
  plan_batch_no VARCHAR(64) NULL,
  stage_code VARCHAR(50) NULL,
  task_type VARCHAR(50) NOT NULL,
  task_name VARCHAR(100) NOT NULL,
  task_source VARCHAR(20) NOT NULL,
  planned_date DATE NULL,
  task_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  task_note VARCHAR(255) NULL,
  completed_at DATETIME(6) NULL,
  completed_by BIGINT NULL,
  completion_note VARCHAR(255) NULL,
  irrigation_record_id BIGINT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (task_id),
  KEY idx_task_plot_date_status (plot_id, planned_date, task_status),
  KEY idx_task_batch (plan_batch_no),
  KEY idx_task_template (template_id),
  KEY idx_task_completed_by (completed_by),
  KEY idx_task_irrigation_record (irrigation_record_id),
  CONSTRAINT fk_farm_task_plot FOREIGN KEY (plot_id) REFERENCES plot (plot_id),
  CONSTRAINT fk_farm_task_template FOREIGN KEY (template_id) REFERENCES cultivation_template (template_id),
  CONSTRAINT fk_farm_task_completed_by FOREIGN KEY (completed_by) REFERENCES users (user_id),
  CONSTRAINT fk_farm_task_irrigation_record FOREIGN KEY (irrigation_record_id) REFERENCES irrigation_record (record_id),
  CONSTRAINT chk_farm_task_source CHECK (task_source IN ('PLAN', 'TEMPORARY')),
  CONSTRAINT chk_farm_task_status CHECK (task_status IN ('PENDING', 'COMPLETED', 'OVERDUE', 'CANCELLED', 'SUPERSEDED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
