-- Stage 1: common audit trail storage for later business stages.
SET NAMES utf8mb4;

CREATE TABLE audit_log (
  log_id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NULL,
  role_code VARCHAR(50) NULL,
  action_type VARCHAR(50) NOT NULL,
  resource_type VARCHAR(50) NOT NULL,
  resource_id VARCHAR(64) NOT NULL,
  description VARCHAR(255) NOT NULL,
  before_data JSON NULL,
  after_data JSON NULL,
  ip_address VARCHAR(64) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (log_id),
  KEY idx_audit_log_user_created (user_id, created_at),
  KEY idx_audit_log_resource (resource_type, resource_id),
  CONSTRAINT fk_audit_log_user FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
