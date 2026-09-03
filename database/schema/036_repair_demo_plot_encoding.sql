-- Repair the one legacy demo plot omitted by 035_refine_demo_presentation_data.sql.
-- The HEX predicate targets only the known latin1-decoded UTF-8 value and will
-- not overwrite a user-renamed plot.
SET NAMES utf8mb4;

UPDATE plot
SET plot_name = '东坡二号果园',
    location = '示范园东区二号梯田',
    crop_name = '脐橙',
    description = '东坡二号标准化脐橙种植区'
WHERE plot_id = 2
  AND farm_id = 1
  AND (
    plot_name = '二号田地'
    OR HEX(plot_name) IN (
      'C3A4C2BAC28CC3A5C28FC2B7C3A7C294C2B0C3A5C29CC2B0',
      'C3A4C2BAC592C3A5C28FC2B7C3A7E2809DC2B0C3A5C593C2B0'
    )
  );
