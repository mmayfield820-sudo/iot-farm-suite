# 数据库结构

`schema` 目录只保留面向交付的最终建表文件，不包含版本迁移或旧字段兼容脚本。二期阶段 1 完成后共 19 张业务表。

- `001_schema.sql`：创建项目所有表、索引、外键和检查约束。
- `002_reference_data.sql`：初始化角色、权限及角色权限关系。

在一期 16 张表基础上，阶段 1 新增：

- `cultivation_template`：奉节脐橙种植管理模板。
- `farm_task`：后续管理计划与农事任务的统一数据底座。
- `audit_log`：关键业务操作审计记录。

同时只扩展 `users`、`farm`、`plot`、`alert` 四张现有表。已有数据库请使用 `database/migrations` 中的有序迁移，不要重新执行建表文件。

Docker 首次创建 MySQL 数据卷时会按顺序自动执行这两个文件，然后执行 `database/seed/001_demo_data.sql`。

在项目根目录一键启动：

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up -d
```

如需从空数据库验证初始化，应使用新的 MySQL 数据卷。不要在包含需保留数据的环境中删除数据卷。

模板中的 `agronomicMoistureTarget` 表示农业标准的田间持水量比例，仅供农业管理参考；设备告警和灌溉控制仍使用 `threshold_config.soil_moisture_threshold`，两者不能直接等同。
