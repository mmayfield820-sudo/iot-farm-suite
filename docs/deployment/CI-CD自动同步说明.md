# CI/CD 自动同步说明（git push 即云端更新）

> 适用：部署完成后的团队迭代。配好之后，成员改动 → `git push` → 云端自动构建更新，**不需要任何人登录服务器**。

---

## 1. 原理

```
团队成员  ── git push ──►  GitHub 仓库
                            │ 触发 GitHub Actions
                            ▼
                    云端服务器（SSH 密钥信任）
                            │ 拉最新代码 + docker compose up -d --build
                            ▼
                    全套服务自动更新（旧容器自动替换）
```

## 2. 一次性配置（负责人做）

### 2.1 准备服务器 SSH 密钥

在**服务器**上生成密钥对（或复用已有的）：

```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions
cat ~/.ssh/github_actions.pub   # 记下公钥
```

### 2.2 在 GitHub 仓库配置 Deploy Key

1. 打开仓库 → Settings → **Deploy keys** → **Add deploy key**
2. Title 填 `deploy-server`
3. Key 粘贴上一步的公钥
4. 勾选 **Allow write access**（服务端要 push 部署状态）

### 2.3 配置 GitHub Actions 密钥（Secret）

仓库 → Settings → **Secrets and variables** → **Actions** → **New repository secret**：

| Name | Value |
|---|---|
| `SERVER_HOST` | 云服务器公网 IP，如 `8.137.105.88` |
| `SERVER_USER` | SSH 用户名，如 `root` |
| `SERVER_SSH_KEY` | 服务器私钥（`~/.ssh/github_actions` 的**完整内容**） |

### 2.4 添加工作流文件

在仓库根目录建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy to server

on:
  push:
    branches: [deploy/fullstack]   # 改为你要自动部署的分支

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd ~/iot-farm-suite
            git pull
            cd infra
            docker compose --env-file ../.env up -d --build
```

## 3. 使用

配置完成后，团队成员只需：

```bash
git push origin deploy/fullstack
```

GitHub Actions 自动执行 → 云端自动更新。可在 GitHub 仓库 **Actions** 标签页看部署进度。

## 4. 注意

- 首次自动部署前，**必须手动部署过一次**（保证 `~/iot-farm-suite` 目录和 `.env` 已在服务器上）。
- `.env` 在服务器上本地维护，不进 Git，所以 `git pull` 不会覆盖它。
- 如果改了 `.env`（如换 key），仍需登录服务器手动改。
