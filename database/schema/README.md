# 数据库结构

这里存放 MySQL 8 建表和数据库升级脚本。文件按数字前缀排序执行，所有成员使用同一套脚本初始化本地数据库。

001_schema.sql 创建表、外键、唯一约束、索引和检查约束；002_reference_data.sql 写入角色和权限基础数据。后续文件为按序执行的升级脚本；008_phase2_account_and_master_data.sql 增加预置账号激活、用户导入暂存、橙园/地块档案字段和地块负责人唯一约束。演示数据位于 database/seed/001_demo_data.sql。

脚本也可以手动执行：

mysql -h 127.0.0.1 -P 3306 -u farm -p farm < database/schema/001_schema.sql

003_mqtt_tracking.sql adds persistent MQTT message deduplication and the command_id field needed to match device command-result messages.

009_phase2_identity_initial_password.sql adds keyed ID-card digests, masked display values, and initial-password reset support for new phase-2 accounts.

012_phase2_template_draft_farm_scope.sql binds each next-cycle draft to the farm whose maintenance window authorizes it.

013_phase2_task_execution_history.sql adds task-adjustment history and one completion record for each planned or ad-hoc task.

014_phase2_stage_moisture_alerts.sql adds the high_moisture alert type used when a production stage's moisture upper bound is exceeded.

015_phase2_plan_adjustment_reminders.sql adds the requirement 4-5 reminders created for low moisture, continuous rain, and offline devices, together with snapshots of affected irrigation or patrol tasks.

016_phase2_plan_adjustment_disposition.sql adds the requirement 4-6 farmer decision and note for each plan-adjustment reminder.
