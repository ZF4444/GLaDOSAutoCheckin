import argparse
import json
import os
import smtplib
import sys
from email.header import Header
from email.mime.text import MIMEText

import dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def perform_checkin(cookie: str, token: str, timeout: int = 30) -> dict:
    url = "https://glados.cloud/api/user/checkin"
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://glados.cloud",
        "referer": "https://glados.cloud/console/checkin",
        "user-agent": (os.environ.get("GLADOS_USER_AGENT") or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"),
        "cookie": cookie,
    }
    data = {"token": token}
    with get_session() as session:
        r = session.post(url, headers=headers, json=data, timeout=timeout)
    return r.json()


def get_status(cookie: str, timeout: int = 30) -> dict:
    url = "https://glados.cloud/api/user/status"
    headers = {
        "accept": "application/json, text/plain, */*",
        "origin": "https://glados.cloud",
        "referer": "https://glados.cloud/console/checkin",
        "user-agent": (os.environ.get("GLADOS_USER_AGENT") or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"),
        "cookie": cookie,
    }
    with get_session() as session:
        r = session.get(url, headers=headers, timeout=timeout)
    return r.json()


def send_email(
    host: str,
    port: int,
    user: str,
    password: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = Header(subject, "utf-8")
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=20)
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
            server.quit()
        else:
            server = smtplib.SMTP(host, port, timeout=20)
            server.ehlo()
            try:
                server.starttls()
                server.ehlo()
            except smtplib.SMTPException:
                pass
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
            server.quit()
    except Exception as e:
        raise RuntimeError(f"邮件发送失败: {e}")


def build_email_content(checkin_resp: dict, status_resp: dict) -> tuple[str, str]:
    code = checkin_resp.get("code")
    message = checkin_resp.get("message") or ""
    data = status_resp.get("data") or {}
    left_days = data.get("leftDays")
    vip = data.get("vip")
    site = data.get("site")
    system_date = data.get("system_date")
    traffic = data.get("traffic")
    def fmt_days(x):
        if x is None:
            return "-"
        try:
            v = float(x)
            s = f"{v:.2f}".rstrip("0").rstrip(".")
            return s
        except Exception:
            return str(x)
    def fmt_traffic(x):
        try:
            v = float(x)
            gb = v / (1024 ** 3)
            return f"{gb:.2f} GB"
        except Exception:
            return "-"
    latest = None
    for item in sorted(checkin_resp.get("list") or [], key=lambda i: i.get("time", 0), reverse=True):
        b = str(item.get("business", ""))
        if b.startswith("system:checkin:"):
            latest = item
            break
    status_text = "成功" if code == 0 else ("重复" if code == 1 else "失败")
    subject = f"GLaDOS签到: {status_text}"
    if left_days is not None:
        subject = f"{subject} | 剩余{fmt_days(left_days)}天"
    body_lines = []
    body_lines.append(f"日期: {system_date or '-'}")
    body_lines.append(f"状态: {status_text}（{message}）")
    body_lines.append(f"剩余天数: {fmt_days(left_days)}")
    if latest:
        body_lines.append(f"今日积分变动: {latest.get('change', '-')}")
        body_lines.append(f"当前积分: {latest.get('balance', '-')}")
    else:
        body_lines.append("今日积分变动: -")
    if vip is not None:
        body_lines.append(f"会员等级: {vip}")
    if site:
        body_lines.append(f"站点: {site}")
    if traffic is not None:
        body_lines.append(f"流量: {fmt_traffic(traffic)}")
    body_lines.append("提示: 每日仅可签到一次")
    return subject, "\n".join(body_lines)


def main():
    dotenv.load_dotenv()

    parser = argparse.ArgumentParser(prog="glados-checkin")
    parser.add_argument("--cookie", default=os.environ.get("GLADOS_COOKIE", ""))
    parser.add_argument("--token", default=os.environ.get("GLADOS_TOKEN", "glados.cloud"))
    parser.add_argument("--smtp-host", default=os.environ.get("EMAIL_SMTP_HOST", ""))
    parser.add_argument("--smtp-port", type=int, default=int(os.environ.get("EMAIL_SMTP_PORT", "587")))
    parser.add_argument("--smtp-user", default=os.environ.get("EMAIL_SMTP_USER", ""))
    parser.add_argument("--smtp-pass", default=os.environ.get("EMAIL_SMTP_PASS", ""))
    parser.add_argument("--from", dest="from_addr", default=os.environ.get("EMAIL_FROM", ""))
    parser.add_argument("--to", dest="to_addr", default=os.environ.get("EMAIL_TO", ""))
    parser.add_argument("--no-email", action="store_true")
    args = parser.parse_args()
    if not args.cookie:
        raise SystemExit("缺少GLADOS_COOKIE")
    checkin_resp = perform_checkin(args.cookie, args.token)
    status_resp = get_status(args.cookie)
    subject, body = build_email_content(checkin_resp, status_resp)
    print(subject)
    print(body)
    exit_status = 0 if checkin_resp.get("code") in (0, 1) else 1
    if args.no_email:
        return exit_status
    must = [args.smtp_host, args.from_addr, args.to_addr]
    if not all(must):
        print("邮件未发送：缺少 EMAIL_SMTP_HOST/EMAIL_FROM/EMAIL_TO 配置")
        return exit_status
    try:
        send_email(
            args.smtp_host,
            args.smtp_port,
            args.smtp_user,
            args.smtp_pass,
            args.from_addr,
            args.to_addr,
            subject,
            body,
        )
        print("邮件发送成功")
        return exit_status
    except Exception as e:
        print(f"邮件发送失败：{e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    sys.exit(main())
