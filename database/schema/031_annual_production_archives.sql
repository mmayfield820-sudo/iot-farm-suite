-- Explicit annual ownership for production archive records.
SET NAMES utf8mb4;

ALTER TABLE management_task
  ADD COLUMN production_year SMALLINT NULL AFTER plot_id,
  ADD KEY idx_task_production_year (production_year, plot_id);

UPDATE management_task AS t
LEFT JOIN management_plan AS p ON p.plan_id = t.plan_id
SET t.production_year = COALESCE(p.production_year, YEAR(DATE_ADD(t.scheduled_date, INTERVAL 1 MONTH)))
WHERE t.production_year IS NULL;

CREATE TABLE farm_production_milestone (
  milestone_id BIGINT NOT NULL AUTO_INCREMENT,
  farm_id BIGINT NOT NULL,
  production_year SMALLINT NOT NULL,
  milestone_type VARCHAR(20) NOT NULL COMMENT 'harvest or cleanup',
  completed_at DATETIME(6) NOT NULL,
  recorded_by BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (milestone_id),
  UNIQUE KEY uk_farm_year_milestone (farm_id, production_year, milestone_type),
  KEY idx_milestone_year_completed (production_year, completed_at),
  CONSTRAINT chk_production_milestone_type CHECK (milestone_type IN ('harvest', 'cleanup')),
  CONSTRAINT fk_production_milestone_farm FOREIGN KEY (farm_id) REFERENCES farm(farm_id),
  CONSTRAINT fk_production_milestone_user FOREIGN KEY (recorded_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Preserve the latest legacy profile values as current-year annual nodes.
INSERT INTO farm_production_milestone
  (farm_id, production_year, milestone_type, completed_at, recorded_by)
SELECT p.farm_id, YEAR(DATE_ADD(p.harvest_completed_at, INTERVAL 1 MONTH)), 'harvest',
       p.harvest_completed_at, p.updated_by
FROM farm_production_profile AS p
WHERE p.harvest_completed_at IS NOT NULL
ON DUPLICATE KEY UPDATE completed_at = VALUES(completed_at), recorded_by = VALUES(recorded_by);

INSERT INTO farm_production_milestone
  (farm_id, production_year, milestone_type, completed_at, recorded_by)
SELECT p.farm_id, YEAR(DATE_ADD(p.harvest_cleanup_completed_at, INTERVAL 1 MONTH)), 'cleanup',
       p.harvest_cleanup_completed_at, p.updated_by
FROM farm_production_profile AS p
WHERE p.harvest_cleanup_completed_at IS NOT NULL
ON DUPLICATE KEY UPDATE completed_at = VALUES(completed_at), recorded_by = VALUES(recorded_by);
