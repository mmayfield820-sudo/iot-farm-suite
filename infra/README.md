# 运行环境

首次使用前，在项目根目录执行 `Copy-Item .env.example .env`，按需修改数据库密码。Docker Desktop 必须已安装并且 Docker Engine 正在运行。

从项目根目录启动 MySQL 8 和 EMQX：

```powershell
docker compose --env-file .env -f infra/docker-compose.yml up -d
```

MySQL 第一次创建数据卷时会自动按顺序执行 `database/schema/` 和 `database/seed/` 中挂载的 SQL。数据库地址为 `127.0.0.1:3306`，默认库名、用户和密码分别为 `farm`、`farm`、`farm`。

查看服务状态：`docker compose --env-file .env -f infra/docker-compose.yml ps`；查看 MySQL 日志：`docker compose --env-file .env -f infra/docker-compose.yml logs -f mysql`。如果需要重新执行初始化脚本，应先确认不再需要数据，再删除 `mysql_data` 数据卷后重新启动。
