-- Stage 1: cultivation rule template. Agricultural capacity ratios are reference values only.
SET NAMES utf8mb4;

CREATE TABLE cultivation_template (
  template_id BIGINT NOT NULL AUTO_INCREMENT,
  template_code VARCHAR(50) NOT NULL,
  template_name VARCHAR(100) NOT NULL,
  variety_name VARCHAR(100) NOT NULL,
  region VARCHAR(100) NOT NULL,
  version INT NOT NULL,
  template_content JSON NOT NULL,
  template_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  created_by BIGINT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (template_id),
  UNIQUE KEY uq_cultivation_template_version (template_code, version),
  KEY idx_cultivation_template_creator (created_by),
  CONSTRAINT fk_cultivation_template_creator FOREIGN KEY (created_by) REFERENCES users (user_id),
  CONSTRAINT chk_cultivation_template_version CHECK (version > 0),
  CONSTRAINT chk_cultivation_template_status CHECK (template_status IN ('ACTIVE', 'INACTIVE'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
