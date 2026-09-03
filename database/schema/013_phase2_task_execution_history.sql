-- Phase 2: farmer task adjustments, completion records, and ad-hoc field work.
SET NAMES utf8mb4;

ALTER TABLE management_task
  ADD COLUMN updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6) AFTER note;

CREATE TABLE management_task_adjustment (
  task_adjustment_id BIGINT NOT NULL AUTO_INCREMENT,
  task_id BIGINT NOT NULL,
  changed_by BIGINT NOT NULL,
  adjustment_type VARCHAR(30) NOT NULL,
  before_value JSON NOT NULL,
  after_value JSON NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (task_adjustment_id),
  KEY idx_task_adjustment_task_created (task_id, created_at),
  CONSTRAINT fk_task_adjustment_task FOREIGN KEY (task_id) REFERENCES management_task(task_id),
  CONSTRAINT fk_task_adjustment_user FOREIGN KEY (changed_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE management_task_completion (
  task_completion_id BIGINT NOT NULL AUTO_INCREMENT,
  task_id BIGINT NOT NULL,
  result VARCHAR(255) NOT NULL,
  executed_at DATETIME(6) NOT NULL,
  executor_user_id BIGINT NOT NULL,
  executor_name VARCHAR(50) NOT NULL,
  note VARCHAR(1000) NULL,
  irrigation_record_id BIGINT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (task_completion_id),
  UNIQUE KEY uq_task_completion_task (task_id),
  KEY idx_task_completion_executed (executed_at),
  CONSTRAINT fk_task_completion_task FOREIGN KEY (task_id) REFERENCES management_task(task_id),
  CONSTRAINT fk_task_completion_user FOREIGN KEY (executor_user_id) REFERENCES users(user_id),
  CONSTRAINT fk_task_completion_irrigation FOREIGN KEY (irrigation_record_id) REFERENCES irrigation_record(record_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
