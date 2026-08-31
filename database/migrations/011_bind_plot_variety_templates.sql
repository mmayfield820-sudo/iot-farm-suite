-- Bind each demo orchard plot to its variety-specific full-cycle template.
SET NAMES utf8mb4;

UPDATE plot p
JOIN cultivation_template t ON t.template_code = CASE p.plot_code
  WHEN 'P001' THEN 'FJ_NAV_72_1'
  WHEN 'P002' THEN 'FJ_NAV_91'
  WHEN 'P003' THEN 'FJ_NAV_95_1'
  WHEN 'P004' THEN 'FJ_HONGCUI_2'
END AND t.version = 1 AND t.template_status = 'ACTIVE'
SET p.template_id = t.template_id,
    p.crop_name = t.variety_name
WHERE p.plot_code IN ('P001', 'P002', 'P003', 'P004');
