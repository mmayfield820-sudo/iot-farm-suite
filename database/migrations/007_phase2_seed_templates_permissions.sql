-- Stage 1: connect new relations and initialize the first cultivation template.
SET NAMES utf8mb4;

ALTER TABLE plot
  ADD CONSTRAINT fk_plot_template FOREIGN KEY (template_id) REFERENCES cultivation_template (template_id);

ALTER TABLE alert
  ADD CONSTRAINT fk_alert_related_task FOREIGN KEY (related_task_id) REFERENCES farm_task (task_id);

SET @system_user_id = (SELECT user_id FROM users WHERE username = 'demo_system' LIMIT 1);

INSERT INTO cultivation_template (
  template_code, template_name, variety_name, region, version, template_content, template_status, created_by
) VALUES (
  'FJ_NAV_GENERIC',
  '奉节脐橙成年结果树通用管理模板',
  '奉节脐橙',
  '重庆市奉节县',
  1,
  JSON_OBJECT(
    'crop', '脐橙',
    'region', '重庆市奉节县',
    'treeClass', 'BEARING_TREE',
    'stages', JSON_ARRAY(
      JSON_OBJECT('code','SPRING_GROWTH','name','萌芽与春季管理期','startMonth',2,'endMonth',3,'managementFocus',JSON_ARRAY('春梢管理','整形修剪'),'tasks',JSON_ARRAY(JSON_OBJECT('type','PRUNING','name','春季整形修剪','offsetDays',7),JSON_OBJECT('type','PATROL','name','春梢生长巡查','offsetDays',3,'repeatDays',14,'repeatUntilStageEnd',TRUE))),
      JSON_OBJECT('code','FLOWERING_FRUIT_SET','name','开花坐果期','startMonth',4,'endMonth',5,'managementFocus',JSON_ARRAY('保花保果'),'tasks',JSON_ARRAY(JSON_OBJECT('type','PATROL','name','花期与坐果巡查','offsetDays',2,'repeatDays',7,'repeatUntilStageEnd',TRUE))),
      JSON_OBJECT('code','YOUNG_FRUIT','name','幼果与夏季管理期','startMonth',6,'endMonth',6,'managementFocus',JSON_ARRAY('病虫害防控'),'tasks',JSON_ARRAY(JSON_OBJECT('type','PEST_CONTROL','name','幼果期病虫害检查','offsetDays',3,'repeatDays',10,'repeatUntilStageEnd',TRUE))),
      JSON_OBJECT('code','FRUIT_EXPANSION','name','果实膨大与秋梢期','startMonth',7,'endMonth',9,'managementFocus',JSON_ARRAY('墒情管理','秋梢管理'),'agronomicMoistureTarget',JSON_OBJECT('basis','FIELD_CAPACITY_RATIO','min',70,'max',80,'irrigateBelow',50),'tasks',JSON_ARRAY(JSON_OBJECT('type','MOISTURE_CHECK','name','果实膨大期墒情检查','offsetDays',0,'repeatDays',7,'repeatUntilStageEnd',TRUE),JSON_OBJECT('type','FERTILIZATION','name','夏季施肥检查','offsetDays',10))),
      JSON_OBJECT('code','MATURITY','name','转色成熟期','startMonth',10,'endMonth',11,'managementFocus',JSON_ARRAY('控水提质','成熟度检查'),'agronomicMoistureTarget',JSON_OBJECT('basis','FIELD_CAPACITY_RATIO','min',30,'max',40),'tasks',JSON_ARRAY(JSON_OBJECT('type','PATROL','name','果实成熟度抽查','offsetDays',3,'repeatDays',10,'repeatUntilStageEnd',TRUE))),
      JSON_OBJECT('code','HARVEST_POSTHARVEST','name','采收及采后管理期','startMonth',11,'endMonth',2,'managementFocus',JSON_ARRAY('分批采收','采后清园'),'tasks',JSON_ARRAY(JSON_OBJECT('type','HARVEST','name','采收准备检查','offsetDays',7),JSON_OBJECT('type','ORCHARD_CLEANUP','name','采后清园巡查','offsetDays',20,'repeatDays',30,'repeatUntilStageEnd',TRUE)))
    )
  ),
  'ACTIVE',
  @system_user_id
);

UPDATE users
SET employee_no = CASE username
    WHEN 'demo_admin' THEN 'DEMO-ADMIN-001'
    WHEN 'demo_farmer' THEN 'DEMO-FARMER-001'
    WHEN 'demo_system' THEN 'DEMO-SYSTEM-001'
    ELSE employee_no
  END,
  activation_status = 'ACTIVATED',
  activated_at = COALESCE(activated_at, UTC_TIMESTAMP(6))
WHERE username IN ('demo_admin', 'demo_farmer', 'demo_system');

UPDATE farm
SET province = '重庆市',
    farm_status = 'ACTIVE',
    area_mu = CASE farm_name
      WHEN '奉节县朱衣橙园' THEN 126.50
      WHEN '奉节县安坪橙园' THEN 84.20
      ELSE area_mu
    END,
    remark = COALESCE(remark, '二期演示橙园')
WHERE farm_name IN ('奉节县朱衣橙园', '奉节县安坪橙园');

SET @template_id = (
  SELECT template_id FROM cultivation_template
  WHERE template_code = 'FJ_NAV_GENERIC' AND version = 1
  LIMIT 1
);

UPDATE plot
SET plot_code = CASE plot_name
      WHEN '朱衣一号果园' THEN 'P001'
      WHEN '朱衣二号果园' THEN 'P002'
      WHEN '朱衣晚熟果园' THEN 'P003'
      WHEN '安坪红翠果园' THEN 'P004'
      ELSE plot_code
    END,
    area_mu = CASE plot_name
      WHEN '朱衣一号果园' THEN 31.20
      WHEN '朱衣二号果园' THEN 28.80
      WHEN '朱衣晚熟果园' THEN 34.50
      WHEN '安坪红翠果园' THEN 22.60
      ELSE area_mu
    END,
    irrigation_method = CASE plot_name
      WHEN '朱衣晚熟果园' THEN '微喷灌'
      ELSE '滴灌'
    END,
    plot_status = 'ACTIVE',
    template_id = @template_id,
    planting_date = CASE plot_name
      WHEN '朱衣一号果园' THEN '2018-03-15'
      WHEN '朱衣二号果园' THEN '2019-03-20'
      WHEN '朱衣晚熟果园' THEN '2017-03-12'
      WHEN '安坪红翠果园' THEN '2024-03-18'
      ELSE planting_date
    END,
    soil_type = CASE plot_name
      WHEN '朱衣二号果园' THEN '冲积土'
      WHEN '安坪红翠果园' THEN '砂壤土'
      ELSE '紫色土'
    END,
    planting_remark = CASE plot_name
      WHEN '安坪红翠果园' THEN '幼树示范区'
      ELSE '成年结果树'
    END
WHERE plot_name IN ('朱衣一号果园', '朱衣二号果园', '朱衣晚熟果园', '安坪红翠果园');
