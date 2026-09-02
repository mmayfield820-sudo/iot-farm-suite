# 打包说明（给队友）

> 本目录负责把仓库打包成「可执行部署包」，交给老师/部署到服务器。
> 每次发布新版本时，**在任意一台能跑 Docker 的机器上重跑一次**即可。

## 〇、日常协作流程（先看这个）

1. **拉最新代码**：`git pull`（改代码前先拉，避免冲突）
2. **改代码** → 本地跑通
3. **推送改动**：
   ```bash
   git add .
   git commit -m "描述你改了什么"
   git push
   ```
   > 分支默认 `deploy/fullstack`，正常 `git push` 就行（推送会自动触发云服务器重新部署）。
4. **只有"要给老师 / 要上线"前**，才需要重新打包（见下文）：
   ```bash
   bash scripts/make_package.sh
   ```

> ⚠️ 记住：**日常改代码只 push，不用打包**；打包是发布时才做的事，每次都要打一次。
> ⚠️ 本机若开着代理/VPN 导致 Docker 构建 npm 下载失败，打包前看「三、打包步骤」的传参说明。

## 一、这是什么

```
scripts/
├── make_package.sh                  ← 一键打包脚本（核心）
└── package/windows/
    ├── 启动.bat / 停止.bat            ← Windows 一键启停（老师双击即用）
    └── 使用说明.txt                   ← 给老师的最简说明
```

打包后得到（产出在 `dist/`）：

```
dist/
├── 预构建镜像包/                     ← 给老师：Windows 双击「启动.bat」即用
│   ├── 启动.bat / 停止.bat / 使用说明.txt / 部署文档.md
│   ├── images/                      5 个镜像（docker load 即用，不联网）
│   └── iot-farm-suite/              ← 只含运行必需文件（不含源码）
│       ├── .env.example             首次启动自动 copy 成 .env
│       ├── infra/docker-compose.yml
│       ├── database/{schema,seed}/*.sql   MySQL 首次启动自动建表 + 演示数据
│       └── device-simulator/鸿蒙模拟器/   模拟器 jar + 预置 sensors.dat（可选喂数据）
└── farm-prebuild.tar.gz              ← 压缩包（传输/上传用）
```

> **发布包内不带平台源码**（backend / frontend / ai-service 等）。镜像里已编译好，运行不需要源码，包也更小（镜像约 530M + 配置文件几 KB）。源码按交付规范单独走 Git 仓库给老师。

## 二、什么时候需要重新打包

改了**任何代码 / compose / 数据库脚本 / 部署文档 / 模拟器数据**之后，发布时就要重打：

```bash
bash scripts/make_package.sh
```

不用每次开发都打，只在"要给老师/要上线"前打一次即可。

## 三、打包步骤（约 10~15 分钟）

```bash
# 1. 在仓库根目录
cd iot-farm-suite

# 2.（可选但推荐）准备 .env —— 不填也能构建，部署时才需要密钥
cp .env.example .env

# 3. 打包（自动完成：构建镜像 → 组装 → 导出 → 校验 → 压缩）
bash scripts/make_package.sh
```

**本机连 npm 下载失败（开着代理/VPN，报 ECONNREFUSED）时**，构建 frontend 需传宿主代理：

```bash
NPM_REGISTRY=https://registry.npmjs.org \
NPM_HTTP_PROXY=http://host.docker.internal:7890 \
bash scripts/make_package.sh
```

（`7890` 换成你 Clash/代理的实际端口。能直连 npmmirror 的机器不用传参，直接跑即可。）

打包过程中会做的事：

| 步骤 | 说明 |
|---|---|
| 构建镜像 | backend / ai-service / frontend 本地构建（frontend npm 源默认 npmmirror，可传参覆盖）；emqx / mysql 从 Docker Hub 拉取 |
| 组装目录 | **白名单复制运行必需文件**：`.env.example` + `docker-compose.yml` + 3 个数据库初始化 SQL + 模拟器（jar + sensors.dat）；不含任何源码、不含 .env |
| 导出镜像 | `docker save \| gzip` 导出 5 个镜像到 `images/` |
| 安全校验 | 确认 `.env` 和敏感文件（复盘/密钥/证书）没有进包，**发现即中止** |
| 压缩 | 用 UTF-8 文件名压缩成 `farm-prebuild.tar.gz` |

## 四、交付方式

| 对象 | 交付物 | 老师怎么用 |
|---|---|---|
| 老师（本机演示） | `dist/预构建镜像包/` 整个目录 | 装 Docker Desktop → 双击「启动.bat」 |
| 老师（云服务器） | `dist/farm-prebuild.tar.gz` | 上传 → 解压 → 按《部署文档》方式 B |
| 老师（先看效果） | 团队云演示 URL | 浏览器直接访问 |

## 五、注意事项（重要）

1. **`.env` 绝不能进包** —— 里面是真实密钥（硅基流动/博查）。脚本白名单不含 .env 并会校验，你自己也不要手动往包里放。
2. **模拟器已随包**：`iot-farm-suite/device-simulator/鸿蒙模拟器/` 里有 jar + 预置好的 `sensors.dat`（6 台设备，UUID 与数据库对齐，老师打开即用）。改了模拟器数据后重打才会进包；`sensors.dat` 被 `.gitignore` 忽略，更新它需 `git add -f`。
3. **镜像架构**：本机打包的镜像是 `x86_64`（Intel/AMD）。老师用普通 Windows/云服务器没问题；若目标机是 **Apple M 系列 Mac 或 ARM 服务器**，镜像跑不起来，需在 ARM 机器上从 Git 仓库拉源码自行 `docker compose build`（源码不进发布包）。
4. **中文文件名编码**：脚本已强制 UTF-8 打包。若你手动 `tar`，务必加 `LANG=C.UTF-8`，否则 Windows/Linux 解压中文名会乱码（老师找不到「启动.bat」）。
5. **改了 Windows 启动脚本**（`scripts/package/windows/`）后要重打，包里的 `启动.bat` 才会更新。
6. **重打会覆盖** `dist/` 下旧产物。

## 六、常见问题

**Q1 构建 frontend 时 npm 下载失败 / 报 `Exit handler never called`**
通常是本机开着代理/VPN 干扰 Docker 出网，tarball 下载被拒（ECONNREFUSED）。解法：按「三、打包步骤」传 `NPM_REGISTRY` + `NPM_HTTP_PROXY` 走宿主代理，或换能直连 npm 的网络。云服务器自动部署不受影响（服务器直连 npmmirror 正常）。

**Q2 报"缺少 .env 但我不想填密钥"**
可以跳过 —— 脚本只用 .env 提供构建参数，缺失时用默认值。真正的密钥是部署时填的。

**Q3 打包出来的 tar 包在 Linux 上解压中文名乱码**
重新用脚本打（脚本已强制 UTF-8）。别用手动 tar。

**Q4 产出的包能发给老师了吗**
先跑 `bash scripts/make_package.sh`（自动过安全校验 + 包内中文名校验）再发最稳；有干净机器的话按《部署文档.md》从解压到登录完整走一遍更好。

**Q5 为什么包里没有 backend/frontend 源码？**
发布包只带运行必需文件（镜像已编译好，运行时不需要源码），避免老师拿到源码，也符合"发布包不放源码、源码单独交付"的规范。最新源码就是 Git 仓库 `deploy/fullstack` 分支。
