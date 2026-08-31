-- Phase 2 refinement: one crop cycle and template assignment per farm.
SET NAMES utf8mb4;

CREATE TABLE farm_production_profile (
  farm_id BIGINT NOT NULL,
  template_version_id BIGINT NOT NULL,
  planting_date DATE NOT NULL,
  tree_age_years DECIMAL(5,2) NULL,
  harvest_cleanup_completed_at DATETIME(6) NULL,
  next_cycle_starts_on DATE NULL,
  note VARCHAR(1000) NULL,
  updated_by BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (farm_id),
  CONSTRAINT chk_farm_profile_tree_age CHECK (tree_age_years IS NULL OR tree_age_years >= 0),
  CONSTRAINT fk_farm_profile_farm FOREIGN KEY (farm_id) REFERENCES farm(farm_id),
  CONSTRAINT fk_farm_profile_template_version FOREIGN KEY (template_version_id) REFERENCES crop_template_version(template_version_id),
  CONSTRAINT fk_farm_profile_user FOREIGN KEY (updated_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- planting_profile remains for migration compatibility. New phase-2 APIs use
-- farm_production_profile; plot-level differences belong to task records and telemetry.
