-- Expand the published S1-S7 orange plan with full-cycle management content.
SET NAMES utf8mb4;

INSERT INTO management_task_template (
  stage_template_id, task_type, title, offset_days, suggested_time, note, track
)
SELECT
  stage.stage_template_id,
  rule_set.task_type,
  rule_set.title,
  rule_set.offset_days,
  NULL,
  rule_set.note,
  rule_set.track
FROM growth_stage_template AS stage
JOIN crop_template_version AS version
  ON version.template_version_id = stage.template_version_id
JOIN crop_template AS template
  ON template.template_id = version.template_id
JOIN (
  SELECT 'S1' AS stage_code, 'pruning' AS task_type, '冬季修剪与清园' AS title, 2 AS offset_days, '结合树势修剪，清除病虫枝、落叶和园内病残体。' AS note, NULL AS track
  UNION ALL SELECT 'S1', 'fertilization', '冬肥与树势检查', 14, '结合土壤和树势核对冬肥安排，避免一次性过量施用。', NULL
  UNION ALL SELECT 'S1', 'inspection', '越冬防冻与设备巡检', 28, '检查树干防冻、排水设施和灌溉设备状态。', NULL
  UNION ALL SELECT 'S2', 'inspection', '春梢萌芽与树势巡查', 0, '记录新梢长度、萌芽整齐度和病虫害情况。', NULL
  UNION ALL SELECT 'S2', 'irrigation', '春季土壤湿度检查', 7, '结合天气和传感器数据判断是否需要补水。', NULL
  UNION ALL SELECT 'S2', 'fertilization', '催芽肥检查', 14, '根据树势和土壤条件核对春季施肥安排。', NULL
  UNION ALL SELECT 'S2', 'pruning', '春季整形修剪检查', 21, '幼树培养树形，结果树疏除交叉枝和弱枝。', NULL
  UNION ALL SELECT 'S2', 'flower_management', '疏除花蕾', 28, '幼树不留花果，减少养分消耗。', 'young'
  UNION ALL SELECT 'S3', 'inspection', '花期与坐果巡查', 0, '记录开花、坐果和异常落花情况。', NULL
  UNION ALL SELECT 'S3', 'flower_management', '摘除幼果', 5, '幼树不留果，保持营养生长。', 'young'
  UNION ALL SELECT 'S3', 'flower_management', '保花保果巡查', 10, '结合花量、树势和天气决定措施。', 'fruiting'
  UNION ALL SELECT 'S3', 'pest_control', '花期病虫害巡查', 20, '重点检查蓟马、红蜘蛛等风险并记录。', NULL
  UNION ALL SELECT 'S4', 'pruning', '夏梢生长检查', 0, '幼树短截抹梢；结果树重点控制旺长夏梢。', NULL
  UNION ALL SELECT 'S4', 'fruit_management', '第一次疏果', 15, '去除小果、病虫果和畸形果。', 'fruiting'
  UNION ALL SELECT 'S4', 'pest_control', '稳果期病虫害巡查', 30, '结合叶片、幼果和天气检查病虫害风险。', NULL
  UNION ALL SELECT 'S5', 'irrigation', '果实膨大期土壤湿度检查', 0, '高温伏旱期结合天气和传感器数据安排灌溉或覆盖。', NULL
  UNION ALL SELECT 'S5', 'inspection', '果实膨大情况巡查', 14, '记录果径、树势和异常落果情况。', 'fruiting'
  UNION ALL SELECT 'S5', 'pruning', '秋梢生长检查', 28, '检查秋梢整齐度，及时处理过密枝和徒长枝。', NULL
  UNION ALL SELECT 'S5', 'fruit_management', '第二次疏果', 45, '按叶果比和树势调整结果负载。', 'fruiting'
  UNION ALL SELECT 'S6', 'pruning', '抹除晚秋梢', 0, '关注 9 月中旬后抽生的新梢。', 'young'
  UNION ALL SELECT 'S6', 'inspection', '转色与成熟度巡查', 0, '结果树关注果实转色、成熟度和病虫害。', 'fruiting'
  UNION ALL SELECT 'S6', 'irrigation', '成熟期土壤湿度检查', 14, '结合天气和树势适度控水，避免持续干旱。', NULL
  UNION ALL SELECT 'S6', 'harvest', '采收准备检查', 35, '核对成熟度、天气、采收工具和人员安排。', 'fruiting'
  UNION ALL SELECT 'S7', 'harvest', '成熟度检查', 0, '果实完全转黄、糖酸比适宜时安排采收。', 'fruiting'
  UNION ALL SELECT 'S7', 'harvest', '采收条件检查', 7, '结合天气、果面状态和储运安排确认采收窗口。', 'fruiting'
  UNION ALL SELECT 'S7', 'cleanup', '采后清园', 14, '清除落果、枯枝和园内废弃物，降低越冬病虫基数。', NULL
  UNION ALL SELECT 'S7', 'inspection', '采后果园与设备巡检', 21, '检查树势恢复、排水和灌溉设备状态。', NULL
) AS rule_set
  ON rule_set.stage_code = stage.stage_code
WHERE version.version_status = 'published'
  AND stage.stage_code IN ('S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7')
  AND (
    SELECT COUNT(*)
    FROM growth_stage_template AS required_stage
    WHERE required_stage.template_version_id = version.template_version_id
      AND required_stage.stage_code IN ('S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7')
  ) = 7
  AND NOT EXISTS (
    SELECT 1
    FROM management_task_template AS existing
    WHERE existing.stage_template_id = stage.stage_template_id
      AND existing.title = rule_set.title
  );
