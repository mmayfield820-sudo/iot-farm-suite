CREATE TABLE plan_change_request (
  request_id BIGINT NOT NULL AUTO_INCREMENT,
  request_no VARCHAR(32) NOT NULL,
  plot_id BIGINT NOT NULL,
  request_type VARCHAR(30) NOT NULL,
  request_source VARCHAR(30) NOT NULL DEFAULT 'FARMER_MANUAL',
  requested_by BIGINT NOT NULL,
  request_reason VARCHAR(255) NOT NULL,
  original_stage_code VARCHAR(50) NULL,
  proposed_stage_code VARCHAR(50) NULL,
  original_plan_batch_no VARCHAR(64) NULL,
  proposed_plan_batch_no VARCHAR(64) NULL,
  before_snapshot JSON NULL,
  after_snapshot JSON NULL,
  request_status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
  submitted_at DATETIME(6) NULL,
  reviewed_by BIGINT NULL,
  reviewed_at DATETIME(6) NULL,
  review_comment VARCHAR(255) NULL,
  applied_at DATETIME(6) NULL,
  rolled_back_at DATETIME(6) NULL,
  version_no INT NOT NULL DEFAULT 1,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (request_id),
  UNIQUE KEY uq_plan_change_request_no (request_no),
  KEY idx_plan_change_plot_status (plot_id, request_status, created_at),
  KEY idx_plan_change_requester (requested_by, created_at),
  KEY idx_plan_change_reviewer (reviewed_by, reviewed_at),
  CONSTRAINT fk_plan_change_plot FOREIGN KEY (plot_id) REFERENCES plot (plot_id),
  CONSTRAINT fk_plan_change_requester FOREIGN KEY (requested_by) REFERENCES users (user_id),
  CONSTRAINT fk_plan_change_reviewer FOREIGN KEY (reviewed_by) REFERENCES users (user_id),
  CONSTRAINT chk_plan_change_type CHECK (request_type IN ('STAGE_OVERRIDE', 'PLANTING_CHANGE', 'PLAN_REGENERATE')),
  CONSTRAINT chk_plan_change_source CHECK (request_source IN ('FARMER_MANUAL', 'SYSTEM_RECOMMENDATION')),
  CONSTRAINT chk_plan_change_status CHECK (request_status IN ('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'ROLLED_BACK', 'CANCELLED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO plan_change_request (
  request_no, plot_id, request_type, request_source, requested_by, request_reason,
  original_stage_code, proposed_stage_code, proposed_plan_batch_no,
  before_snapshot, after_snapshot, request_status, submitted_at, applied_at, created_at
)
SELECT CONCAT('PCR-MIG-A', a.alert_id), a.plot_id, 'STAGE_OVERRIDE', 'FARMER_MANUAL',
       COALESCE(p.stage_override_by, p.farmer_user_id),
       COALESCE(NULLIF(p.stage_override_reason, ''), a.alert_description),
       JSON_UNQUOTE(JSON_EXTRACT(l.before_data, '$.currentStage.stageCode')),
       p.stage_override_code,
       (SELECT ft.plan_batch_no FROM farm_task ft WHERE ft.plot_id=a.plot_id AND ft.plan_batch_no IS NOT NULL ORDER BY ft.task_id DESC LIMIT 1),
       COALESCE(l.before_data, JSON_OBJECT()), COALESCE(l.after_data, JSON_OBJECT()),
       'PENDING_REVIEW', a.alert_datetime, a.alert_datetime, a.alert_datetime
FROM alert a
JOIN plot p ON p.plot_id=a.plot_id
LEFT JOIN audit_log l ON l.log_id=(
  SELECT l2.log_id FROM audit_log l2
  WHERE l2.resource_type='PLOT_STAGE' AND l2.resource_id=CONCAT('P', LPAD(a.plot_id, 3, '0'))
  ORDER BY l2.log_id DESC LIMIT 1
)
WHERE a.alert_type='plan_adjustment';

DELETE FROM alert WHERE alert_type='plan_adjustment';

ALTER TABLE alert
  DROP FOREIGN KEY fk_alert_related_task,
  DROP CHECK chk_alert_resolution_action,
  DROP CHECK chk_alert_type,
  DROP INDEX idx_alert_related_task,
  DROP COLUMN related_task_id,
  DROP COLUMN resolution_action,
  DROP COLUMN resolution_remark,
  ADD CONSTRAINT chk_alert_type CHECK (alert_type IN ('low_moisture', 'device_offline', 'device_fault', 'irrigation_failed', 'continuous_rain'));
