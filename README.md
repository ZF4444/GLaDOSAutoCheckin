# GLaDOS 自动签到工具

支持部署在无头 Ubuntu，使用 Cookie 进行签到，并通过邮件发送结果。

## 功能
- 访问 `https://glados.cloud/api/user/checkin` 完成每日签到
- 查询 `https://glados.cloud/api/user/status` 获取剩余天数
- 通过 SMTP 邮件发送签到结果与剩余天数
- 适配无头环境（不需要浏览器或桌面）

## 环境准备
1. 安装 Python 3.9+ 与 pip
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip
   ```
2. 安装依赖
   ```bash
   pip3 install -r requirements.txt
   ```

## 使用 uv 管理运行环境（推荐）

本项目依赖较少，适合使用 uv 管理 Python 虚拟环境，再通过 cron 定时执行，无需部署 Docker。uv 安装方式见[官方安装文档](https://docs.astral.sh/uv/getting-started/installation/)。

### 方式一：保留 requirements.txt

在项目目录执行：

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
```

配置好下文的 `.env` 后，使用虚拟环境中的 Python 运行：

```bash
.venv/bin/python checkin.py
```

无需激活虚拟环境。此方式不改变现有项目结构。

### 方式二：使用 uv 项目管理

如需锁定依赖版本、方便在其他机器重建环境，可以在项目目录初始化 uv 项目：

```bash
uv init --bare --python 3.12
uv add -r requirements.txt
uv sync --locked
```

配置好 `.env` 后运行：

```bash
uv run checkin.py
```

将生成的 `pyproject.toml`、`uv.lock` 和 `.python-version` 提交到 Git，不提交 `.venv` 和包含凭据的 `.env`。其他机器安装 uv 后，在项目目录执行 `uv sync --locked` 即可按锁文件创建环境。

以上两种方式任选其一。长期维护推荐方式二；部署时先安装或同步依赖，定时任务直接调用 `.venv/bin/python`。

## 使用 .env 配置
- 新建 `.env` 文件（可参考 `.env.example`）：
  ```
  GLADOS_COOKIE=koa:sess=...; koa:sess.sig=...
  GLADOS_TOKEN=glados.cloud
  EMAIL_SMTP_HOST=smtp.example.com
  EMAIL_SMTP_PORT=587
  EMAIL_SMTP_USER=user@example.com
  EMAIL_SMTP_PASS=your_app_password
  EMAIL_FROM=user@example.com
  EMAIL_TO=receiver@example.com
  ```
- 脚本会自动加载当前目录下的 `.env`
- 运行：
  ```bash
  python3 checkin.py
  ```

## 获取 GLaDOS Cookie
1. 浏览器打开 `https://glados.cloud/console/checkin` 并登录
2. 打开开发者工具 Network 标签
3. 刷新页面，找到名为 `status` 的网络请求
4. 在该请求的 Request Headers 中复制 `Cookie` 字段（通常形如 `koa:sess=...; koa:sess.sig=...`）

## 运行
通过环境变量或命令行参数进行配置。

环境变量：
- `GLADOS_COOKIE` 复制自浏览器的 Cookie
- `GLADOS_USER_AGENT` 登录时浏览器的 User-Agent，应与 Cookie 来自同一浏览器
- `GLADOS_TOKEN` 可选，默认 `glados.cloud`
- `EMAIL_SMTP_HOST` SMTP 主机，如 `smtp.gmail.com`
- `EMAIL_SMTP_PORT` SMTP 端口，465 使用 SSL，587 使用 STARTTLS
- `EMAIL_SMTP_USER` SMTP 用户名
- `EMAIL_SMTP_PASS` SMTP 密码或应用专用密码
- `EMAIL_FROM` 发件人邮箱
- `EMAIL_TO` 收件人邮箱

命令行示例：
```bash
GLADOS_COOKIE="koa:sess=...; koa:sess.sig=..." \
EMAIL_SMTP_HOST=smtp.example.com \
EMAIL_SMTP_PORT=587 \
EMAIL_SMTP_USER=user@example.com \
EMAIL_SMTP_PASS=your_app_password \
EMAIL_FROM=user@example.com \
EMAIL_TO=receiver@example.com \
python3 checkin.py
```

也可使用参数：
```bash
python3 checkin.py \
  --cookie "koa:sess=...; koa:sess.sig=..." \
  --smtp-host smtp.example.com \
  --smtp-port 587 \
  --smtp-user user@example.com \
  --smtp-pass your_app_password \
  --from user@example.com \
  --to receiver@example.com
```

若只测试不发送邮件：
```bash
python3 checkin.py --cookie "koa:sess=...; koa:sess.sig=..." --no-email
```

## 定时任务（cron）
### uv 虚拟环境方式（推荐）

完成上述 uv 环境准备及 `.env` 配置后，先手动运行 `.venv/bin/python checkin.py`，确认签到及邮件发送正常。

在项目目录执行 `mkdir -p logs`，然后运行 `crontab -e`，添加以下**单行**配置，每天 9:30 执行（将 `/path/to/GLaDOSAutoCheckin` 替换为实际项目绝对路径）：

```cron
30 9 * * * cd /path/to/GLaDOSAutoCheckin && /path/to/GLaDOSAutoCheckin/.venv/bin/python -u checkin.py >> /path/to/GLaDOSAutoCheckin/logs/checkin.log 2>&1
```

脚本自动读取项目中的 `.env`，无需在 crontab 中重复填写 Cookie 和邮件密码。定时任务无需激活虚拟环境，也无需每次重新安装依赖。执行时间按服务器配置的时区计算；普通 cron 不会补执行关机期间错过的任务。

### 系统 Python 方式

1. 创建日志目录
   ```bash
   mkdir -p logs
   ```
2. 编辑 crontab
   ```bash
   crontab -e
   ```
3. 添加每日 9:30 执行任务（根据需要调整路径与时间）
   ```cron
   30 9 * * * cd /path/to/AutoCheckin && \
   GLADOS_COOKIE='koa:sess=...; koa:sess.sig=...' \
   EMAIL_SMTP_HOST='smtp.example.com' \
   EMAIL_SMTP_PORT='587' \
   EMAIL_SMTP_USER='user@example.com' \
   EMAIL_SMTP_PASS='your_app_password' \
   EMAIL_FROM='user@example.com' \
   EMAIL_TO='receiver@example.com' \
   /usr/bin/python3 checkin.py >> logs/checkin.log 2>&1
   ```

## 邮件发送注意
- 使用 Gmail 等服务时，建议使用应用专用密码
- 端口 465 使用 SSL，端口 587 使用 STARTTLS
- 若无需认证，可留空 `EMAIL_SMTP_USER` 与 `EMAIL_SMTP_PASS`

## 失败排查
- 没有权限：检查 `GLADOS_COOKIE` 是否有效、是否过期
- 签到失败：尝试将 `GLADOS_TOKEN` 设置为 `glados.cloud` 或站点当前使用的 token
- 网络错误：在服务器上确认能访问 `https://glados.rocks/api/user/status`

## Cookie 与 User-Agent 配置

直接请求方案无需安装或运行浏览器。在 `.env` 中设置 `GLADOS_USER_AGENT`，与获取 Cookie 时的浏览器一致，避免 `device-mismatch`。可在该浏览器开发者工具 Console 执行 `navigator.userAgent` 获取。

```dotenv
GLADOS_COOKIE="koa:sess=...; koa:sess.sig=..."
GLADOS_USER_AGENT="获取 Cookie 时浏览器的完整 User-Agent"
GLADOS_TOKEN=glados.cloud
```

Cookie 过期后重新登录并更新 Cookie；切换浏览器时同时更新 User-Agent。此配置不保证网站始终允许自动签到。

当前已验证匹配的 Cookie 和 User-Agent 能通过直接请求返回“今日已签到”，首次签到仍待次日验证。签到失败时脚本返回非零退出码，便于定时任务识别失败。
