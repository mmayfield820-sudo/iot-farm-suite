-- Stage 3: add executable management tasks to the first cultivation template.
SET NAMES utf8mb4;

UPDATE cultivation_template
SET template_content = JSON_SET(
  template_content,
  '$.stages[0].managementFocus', JSON_ARRAY('春梢管理','整形修剪'),
  '$.stages[0].tasks', JSON_ARRAY(JSON_OBJECT('type','PRUNING','name','春季整形修剪','offsetDays',7),JSON_OBJECT('type','PATROL','name','春梢生长巡查','offsetDays',3,'repeatDays',14,'repeatUntilStageEnd',TRUE)),
  '$.stages[1].managementFocus', JSON_ARRAY('保花保果'),
  '$.stages[1].tasks', JSON_ARRAY(JSON_OBJECT('type','PATROL','name','花期与坐果巡查','offsetDays',2,'repeatDays',7,'repeatUntilStageEnd',TRUE)),
  '$.stages[2].managementFocus', JSON_ARRAY('病虫害防控'),
  '$.stages[2].tasks', JSON_ARRAY(JSON_OBJECT('type','PEST_CONTROL','name','幼果期病虫害检查','offsetDays',3,'repeatDays',10,'repeatUntilStageEnd',TRUE)),
  '$.stages[3].managementFocus', JSON_ARRAY('墒情管理','秋梢管理'),
  '$.stages[3].tasks', JSON_ARRAY(JSON_OBJECT('type','MOISTURE_CHECK','name','果实膨大期墒情检查','offsetDays',0,'repeatDays',7,'repeatUntilStageEnd',TRUE),JSON_OBJECT('type','FERTILIZATION','name','夏季施肥检查','offsetDays',10)),
  '$.stages[4].managementFocus', JSON_ARRAY('控水提质','成熟度检查'),
  '$.stages[4].tasks', JSON_ARRAY(JSON_OBJECT('type','PATROL','name','果实成熟度抽查','offsetDays',3,'repeatDays',10,'repeatUntilStageEnd',TRUE)),
  '$.stages[5].managementFocus', JSON_ARRAY('分批采收','采后清园'),
  '$.stages[5].tasks', JSON_ARRAY(JSON_OBJECT('type','HARVEST','name','采收准备检查','offsetDays',7),JSON_OBJECT('type','ORCHARD_CLEANUP','name','采后清园巡查','offsetDays',20,'repeatDays',30,'repeatUntilStageEnd',TRUE))
)
WHERE template_code='FJ_NAV_GENERIC' AND version=1;
