# 数据库升级脚本

此目录仅用于已有一期数据库的原地升级。脚本按文件名前缀顺序执行，每个脚本只执行一次：

1. `003_phase2_alter_core_tables.sql`
2. `004_phase2_create_cultivation_template.sql`
3. `005_phase2_create_farm_task.sql`
4. `006_phase2_create_audit_log.sql`
5. `007_phase2_seed_templates_permissions.sql`
6. `008_phase2_seed_template_tasks.sql`
7. `009_phase2_plan_adjustment_rollback.sql`
8. `010_phase2_plan_change_request.sql`
9. `011_bind_plot_variety_templates.sql`

执行前必须先备份数据库。全新环境不要运行这些迁移，直接依次执行 `database/schema/001_schema.sql`、`database/schema/002_reference_data.sql` 和 `database/seed/001_demo_data.sql`。

`010` 将计划变更从普通告警中拆分到独立申请表，并迁移已有计划调整数据；执行后普通告警表只保存设备和农田异常。

`011` 在四个品种模板已经导入后，将 P001～P004 分别绑定到奉园72-1、奉园91、奉节晚橙95-1和红翠2号模板。
