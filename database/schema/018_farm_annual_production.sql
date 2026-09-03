-- Annual production management for a uniformly planted orchard.
SET NAMES utf8mb4;

ALTER TABLE farm
  ADD COLUMN planting_date DATE NULL COMMENT 'Actual orchard planting date, confirmed after farmers complete planting tasks';

UPDATE farm AS f
JOIN farm_production_profile AS p ON p.farm_id = f.farm_id
SET f.planting_date = p.planting_date
WHERE f.planting_date IS NULL;

ALTER TABLE management_task_template
  ADD COLUMN track VARCHAR(20) NULL COMMENT 'young, fruiting, or NULL for a shared suggestion';

CREATE TABLE IF NOT EXISTS farm_annual_production (
  annual_production_id BIGINT NOT NULL AUTO_INCREMENT,
  farm_id BIGINT NOT NULL,
  production_year SMALLINT NOT NULL COMMENT 'December of prior year through November of this year',
  template_version_id BIGINT NOT NULL,
  orchard_track VARCHAR(20) NOT NULL COMMENT 'young or fruiting',
  track_source VARCHAR(20) NOT NULL DEFAULT 'auto' COMMENT 'auto or extended_young',
  track_override_reason VARCHAR(500) NULL,
  annual_status VARCHAR(20) NOT NULL DEFAULT 'published',
  created_by BIGINT NULL,
  updated_by BIGINT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (annual_production_id),
  UNIQUE KEY uk_farm_annual_production (farm_id, production_year),
  KEY idx_annual_production_template (template_version_id),
  CONSTRAINT fk_annual_production_farm FOREIGN KEY (farm_id) REFERENCES farm(farm_id),
  CONSTRAINT fk_annual_production_template FOREIGN KEY (template_version_id) REFERENCES crop_template_version(template_version_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
