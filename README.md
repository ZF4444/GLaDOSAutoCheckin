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

## 使用 .env 配置
- 新建 `.env` 文件（可参考 `.env.example`）：
  ```
  GLADOS_COOKIE=koa:sess=...; koa:sess.sig=...
  GLADOS_TOKEN=glados.one
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
- `GLADOS_TOKEN` 可选，默认 `glados.one`
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
- 签到失败：尝试将 `GLADOS_TOKEN` 设置为 `glados.one` 或站点当前使用的 token
- 网络错误：在服务器上确认能访问 `https://glados.rocks/api/user/status`
