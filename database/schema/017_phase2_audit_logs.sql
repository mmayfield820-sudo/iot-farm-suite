-- Phase 2 requirement 5-7: durable audit records for key business operations.
CREATE TABLE audit_log (
  audit_log_id BIGINT NOT NULL AUTO_INCREMENT,
  actor_user_id BIGINT NOT NULL,
  module_code VARCHAR(40) NOT NULL,
  action_code VARCHAR(60) NOT NULL,
  target_type VARCHAR(40) NULL,
  target_id VARCHAR(80) NULL,
  detail VARCHAR(1000) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (audit_log_id),
  KEY idx_audit_log_created_at (created_at),
  KEY idx_audit_log_module_created_at (module_code, created_at),
  KEY idx_audit_log_actor_created_at (actor_user_id, created_at),
  CONSTRAINT fk_audit_log_actor FOREIGN KEY (actor_user_id) REFERENCES users (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
