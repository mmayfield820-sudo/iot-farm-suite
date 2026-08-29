# 数据库结构

`schema` 目录只保留面向交付的最终建表文件，不包含版本迁移或旧字段兼容脚本。

- `001_schema.sql`：创建项目所有表、索引、外键和检查约束。
- `002_reference_data.sql`：初始化角色、权限及角色权限关系。

Docker 首次创建 MySQL 数据卷时会按顺序自动执行这两个文件，然后执行 `database/seed/001_demo_data.sql`。

在项目根目录一键启动：

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up -d
```

如需从空数据库验证初始化，应使用新的 MySQL 数据卷。不要在包含需保留数据的环境中删除数据卷。
