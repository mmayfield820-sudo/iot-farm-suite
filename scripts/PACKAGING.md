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
   > 分支默认 `deploy/fullstack`，正常 `git push` 就行。
4. **只有"要给老师 / 要上线"前**，才需要重新打包（见下文）：
   ```bash
   bash scripts/make_package.sh
   ```

> ⚠️ 记住：**日常改代码只 push，不用打包**；打包是发布时才做的事，每次都要打一次。

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
│   ├── 启动.bat 停止.bat 使用说明.txt
│   ├── images/                      5 个镜像（docker load 即用，不联网）
│   ├── iot-farm-suite/              源码 + compose + 数据库脚本
│   └── 部署文档.md
└── farm-prebuild.tar.gz              ← 上传云服务器用（部署文档 · 方式 B）
```

## 二、什么时候需要重新打包

改了**任何代码 / compose / 数据库脚本 / 文档**之后，发布时就要重打：

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

打包过程中会做的事：

| 步骤 | 说明 |
|---|---|
| 构建镜像 | backend / ai-service / frontend 本地构建；emqx / mysql 从 Docker Hub 拉取 |
| 组装目录 | 复制源码（**自动排除 .env、.git、node_modules、模拟器、视频**）+ Windows 启动文件 + 部署文档 |
| 导出镜像 | `docker save \| gzip` 导出 5 个镜像到 `images/` |
| 安全校验 | 确认 `.env` 和敏感文件没有进包，**发现即中止** |
| 压缩 | 用 UTF-8 文件名压缩成 `farm-prebuild.tar.gz` |

## 四、交付方式

| 对象 | 交付物 | 老师怎么用 |
|---|---|---|
| 老师（本机演示） | `dist/预构建镜像包/` 整个目录 | 装 Docker Desktop → 双击「启动.bat」 |
| 老师（云服务器） | `dist/farm-prebuild.tar.gz` | 上传 → 解压 → 按《部署文档》方式 B |
| 老师（先看效果） | 团队云演示 URL | 浏览器直接访问 |

## 五、注意事项（重要）

1. **`.env` 绝不能进包** —— 里面是真实密钥（硅基流动/博查）。脚本已自动排除并校验，但你自己也不要手动往包里放。
2. **镜像架构**：本机打包的镜像是 `x86_64`（Intel/AMD）。老师用普通 Windows/云服务器没问题；若老师是 **Apple M 系列 Mac 或 ARM 服务器**，镜像跑不起来，用「源码包」让 Docker 自动构建对应架构（见部署文档）。
3. **中文文件名编码**：脚本已强制 UTF-8 打包。若你手动 `tar`，务必加 `LANG=C.UTF-8`，否则 Windows/Linux 解压中文名会乱码（老师找不到「启动.bat」）。
4. **改了 Windows 启动脚本**（`scripts/package/windows/`）后要重打，包里的 `启动.bat` 才会更新。
5. **重打会覆盖** `dist/` 下旧产物。

## 六、常见问题

**Q1 构建时 npm 下载超时**
前端 Dockerfile 里已配置国内镜像源兜底，多试一次即可；或把 Docker Desktop 的代理配好。

**Q2 报"缺少 .env 但我不想填密钥"**
可以跳过 —— 脚本只用 .env 提供构建参数，缺失时用默认值。真正的密钥是部署时填的。

**Q3 打包出来的 tar 包在 Linux 上解压中文名乱码**
重新用脚本打（脚本已强制 UTF-8）。别用手动 tar。

**Q4 产出的包能发给老师了吗**
先跑 `bash scripts/make_package.sh` 里的校验，再按《部署文档.md》的「部署核对清单」自测一遍最稳。
