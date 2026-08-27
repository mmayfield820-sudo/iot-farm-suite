# 后端

后端业务服务、数据库访问、MQTT 接入和 WebSocket 推送代码放在这里。接口以
`../contracts/openapi.yaml` 为准，数据库结构以
`../database/schema/smart_agriculture.sql` 为准。

## 当前状态

- 编程语言：Python
- 数据库：MySQL，数据库由 SQL Workbench 管理
- Python 数据库访问：SQLAlchemy + PyMySQL
- 配置读取：python-dotenv
- Web 框架：尚未确定

当前已经创建数据库连接基础层，但还没有连接 API、业务模块或启动服务器。

## 目录结构

```text
backend/
├── src/
│   ├── config/
│   │   └── settings.py          # 数据库和应用配置
│   ├── database/
│   │   ├── connection.py        # SQLAlchemy Engine 和 Session 工厂
│   │   ├── models/              # 数据库模型
│   │   └── repositories/        # 数据访问对象
│   ├── modules/                 # auth、farm、device 等业务模块
│   ├── mqtt/                    # MQTT 连接和消息处理
│   └── websocket/               # 实时事件推送
├── tests/                       # 后端单元测试和接口测试
└── README.md
```

详细说明见 [backend 目录与文件说明](目录与文件说明.md)。

## 数据库连接配置

复制项目根目录的 `.env.example` 为 `.env`，填写 SQL Workbench 所连接的 MySQL 实例信息：

```text
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=smart_agriculture
```

连接 URL 会由程序安全地拼接，密码中的特殊字符不需要手动 URL 编码。`.env` 已被 Git 忽略，
不要将真实密码提交到仓库。
