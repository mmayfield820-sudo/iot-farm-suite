# EMQX 部署与同步说明

> 本文件说明：MQTT 中间件（EMQX）是什么、怎么部署、怎么用控制台、以及组员需要同步哪些信息。
> 配套：[MQTT主题与数据格式规范.md](./MQTT主题与数据格式规范.md)（主题 + JSON 字段约定）、[docker-compose.yml](./docker-compose.yml)（启动配置）。

---

## 1. EMQX 是什么

**MQTT 消息代理（Broker）**：负责在「设备」和「后端」之间转发消息。传感器把数据发到它，后端从它订阅；后端把控制指令发到它，设备从它订阅。

---

## 2. 部署结果

| 项       | 值                    |
| ------- | -------------------- |
| 部署方式    | Docker 容器，名称 `emqx`  |
| 配置文件    | `docker-compose.yml` |
| 版本      | EMQX 6.2.3           |
| MQTT 端口 | `1883`               |
| 控制台端口   | `18083`              |
| 认证      | 暂不配（匿名连接）            |
| 集群      | 单节点（**不需要集群**）       |

---

## 3. 控制台（Dashboard）是什么、怎么看

- **是什么**：EMQX 的图形化管理网页，能看到连接数、客户端、主题、消息、运行状态。
- **怎么打开**：浏览器输入 `http://localhost:18083`
- **登录**：账号 `admin`，密码 `public`（首次登录会强制改一次密码）

> 用途：联调时，模拟器发数据、后端收数据，都能在这里**肉眼确认消息在不在流动**，是排错神器。

---

## 4. 需不需要集群？

**不需要。** 集群是企业级场景（百万级连接、高可用、负载均衡）才需要的。本项目是 6 人学生项目 + 几台模拟设备，**单节点完全够用**。

---

## 5. 同步信息清单（部署者发到群里）

| #   | 同步内容         | 值                                                         |
| --- | ------------ | --------------------------------------------------------- |
| 1   | MQTT 地址 + 端口 | `127.0.0.1:1883`                                          |
| 2   | 控制台地址        | `http://localhost:18083`（账号 admin，密码自定）                   |
| 3   | 认证方式         | 暂不配账号密码（匿名连接）                                             |
| 4   | 主题 + JSON 规范 | 见《MQTT主题与数据格式规范.md》                                       |
| 5   | 启动文件         | `docker-compose.yml`（clone 后 `docker compose up -d`）      |
| 6   | 开发规则         | **需要用到的人本地各起一个 EMQX**，都连 `127.0.0.1:1883`，互不干扰；联调期再统一连同一台 |

---

## 6. 部署操作步骤（用 docker-compose.yml）

1. **启动 Docker Desktop**（等任务栏小鲸鱼图标变绿色）。

2. **拿到项目代码**（clone 仓库，确保目录里有 `docker-compose.yml`）。

3. **在项目目录执行**：
   
   ```bash
   docker compose up -d
   ```
   
   这一条命令会自动拉取镜像并启动 EMQX 容器。

4. **验证**：
   
   ```bash
   docker compose ps        # 看到 emqx，STATUS 是 Up
   ```
   
   浏览器打开 `http://localhost:18083`，能打开登录页 = 成功。

5. **常用管理命令**：
   
   ```bash
   docker compose up -d       # 启动（容器不存在会先创建）
   docker compose stop        # 停止
   docker compose start       # 启动已停止的容器
   docker compose restart     # 重启
   docker compose logs emqx   # 看日志
   docker compose down        # 停止并删除容器（删了重跑第 3 步）
   ```

> 备选：如果不想用 compose，也可以用裸命令 `docker run -d --name emqx --restart unless-stopped -p 1883:1883 -p 18083:18083 emqx/emqx`，效果一样。**但建议统一用 compose**，方便版本管理和 F 后续集成。
> 
> 注意：如果之前已经用 `docker run` 起过一个叫 `emqx` 的容器，先 `docker rm -f emqx` 删掉，再用 compose 起，避免容器名冲突。

---

## 7. 常见问题

| 现象                               | 原因                           | 解决                               |
| -------------------------------- | ---------------------------- | -------------------------------- |
| `docker compose up` 报 daemon 未运行 | Docker Desktop 没启动           | 先启动 Docker Desktop               |
| 容器名冲突 `emqx` 已存在                 | 之前用 `docker run` 起过          | `docker rm -f emqx` 再 compose up |
| 脚本连不上 1883                       | 端口被占 / 容器没起                  | `docker compose ps` 检查；换端口       |
| 控制台打不开                           | 端口没映射 / 容器没起                 | 确认 `-p 18083:18083` 和容器状态        |
| 重启电脑后 broker 没了                  | 没加 `restart: unless-stopped` | 确认 compose 里已配置（本文件已配）           |

---

*关联：[MQTT主题与数据格式规范.md](./MQTT主题与数据格式规范.md)、[docker-compose.yml](./docker-compose.yml)、[分工协作与接口对接.md](./分工协作与接口对接.md)、[E_任务指导书.md](./E_任务指导书.md)。*
