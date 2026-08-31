# 数据库交付说明

本目录以交付时正在运行的 MySQL `farm` 数据库为事实来源，已经合并历史迁移结果，可从空库一次性恢复为当前项目使用的数据状态。

## 目录内容

- `schema/001_schema.sql`：当前 20 张表的最终结构、索引、外键和检查约束。
- `schema/002_reference_data.sql`：当前角色、权限和角色权限关系。
- `seed/001_demo_data.sql`：当前业务数据一致性快照。
- `design/当前数据库说明.docx`：字段、取值、主外键、业务关系与数据概况说明。
- `backups/`：开发者本机备份目录，SQL 快照由 `.gitignore` 排除，不属于版本库交付物。

历史迁移脚本和旧设计说明已移除。后续如需调整数据库，应先同步修改最终结构/快照和说明文档；若要支持已部署环境升级，可在新的迭代中单独建立迁移方案，不要把旧迁移重新混入本次交付基线。

## Docker 初始化

首次创建 MySQL 数据卷时，`infra/docker-compose.yml` 会依次执行：

1. `schema/001_schema.sql`
2. `schema/002_reference_data.sql`
3. `seed/001_demo_data.sql`

在项目根目录启动：

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up -d
```

初始化脚本只适用于空数据库。已有数据需要保留时，不要重复执行，也不要删除现有 MySQL 数据卷。

## 手工恢复到空库

```powershell
Get-Content database/schema/001_schema.sql, database/schema/002_reference_data.sql, database/seed/001_demo_data.sql |
  mysql -h 127.0.0.1 -P 3306 -u root -p farm
```

## 当前演示账号

| 用户名 | 姓名 | 角色 | 激活状态 |
| --- | --- | --- | --- |
| `demo_admin` | 张园长 | 农场管理员 | 待激活 |
| `demo_farmer` | 李果农 | 农户 | 已激活 |
| `demo_system` | 王管理员 | 系统管理员 | 已激活 |

账号密码不在 README 中保存明文；测试凭据按项目现有登录说明或初始化约定使用。

## 激活测试
工号：DEMO-ADMIN-001
手机号：13800000001
激活码：xdaa31qSSJ0
激活入口：/activation
角色：农场管理员
管理范围：F001、F002