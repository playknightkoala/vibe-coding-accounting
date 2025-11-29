import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


from typing import Union, List

def send_email(to_email: Union[str, List[str]], subject: str, html_content: str) -> bool:
    """
    使用 Gmail SMTP 發送郵件

    Args:
        to_email: 收件人郵箱 (單個字串或字串列表)
        subject: 郵件主題
        html_content: HTML 郵件內容

    Returns:
        bool: 發送成功返回 True，失敗返回 False
    """
    try:
        # 處理收件人列表
        if isinstance(to_email, list):
            to_emails_str = ", ".join(to_email)
            to_emails_list = to_email
        else:
            to_emails_str = to_email
            to_emails_list = [to_email]

        # 建立郵件
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_emails_str

        # 加入 HTML 內容
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # 連接 Gmail SMTP 伺服器
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()  # 啟用 TLS 加密
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)

        logger.info(f"Email sent successfully to {to_emails_str}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """
    發送密碼重設郵件

    Args:
        to_email: 收件人郵箱
        reset_token: 密碼重設 token

    Returns:
        bool: 發送成功返回 True，失敗返回 False
    """
    # 建立重設連結
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    # HTML 郵件內容
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #e0e0e0;
                background-color: #1a1a2e;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
                padding: 40px 20px;
                text-align: center;
                border-bottom: 2px solid #00d4ff;
            }}
            .header h1 {{
                color: #00d4ff;
                margin: 0;
                font-size: 28px;
                text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
            }}
            .content {{
                padding: 40px 30px;
            }}
            .content p, .content ul, .content li {{
                margin: 0 0 20px;
                color: #a0aec0;
            }}
            .button {{
                display: inline-block;
                padding: 15px 40px;
                background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
                color: #ffffff !important;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
                transition: all 0.3s ease;
            }}
            .button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
            }}
            .footer {{
                background-color: #0f3460;
                padding: 20px;
                text-align: center;
                color: #6b7280;
                font-size: 14px;
                border-top: 1px solid #00d4ff;
            }}
            .warning {{
                background-color: rgba(255, 107, 107, 0.1);
                border-left: 4px solid #ff6b6b;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .info-box {{
                background-color: rgba(0, 212, 255, 0.1);
                border-left: 4px solid #00d4ff;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 密碼重設請求</h1>
            </div>
            <div class="content">
                <p>您好，</p>
                <p>我們收到了您的密碼重設請求。請點擊下方按鈕重設您的密碼：</p>

                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">重設密碼</a>
                </div>

                <div class="info-box">
                    <p style="margin: 0;"><strong>📌 注意事項：</strong></p>
                    <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                        <li>此連結將在 {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} 分鐘後失效</li>
                        <li>連結僅可使用一次</li>
                        <li>新密碼必須符合安全性要求</li>
                    </ul>
                </div>

                <p style="margin-top: 20px;">如果上方按鈕無法點擊，請複製以下連結到瀏覽器：</p>
                <p style="word-break: break-all; background-color: rgba(0, 212, 255, 0.05); padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px;">
                    {reset_link}
                </p>

                <div class="warning">
                    <p style="margin: 0;"><strong>⚠️ 安全提醒：</strong></p>
                    <p style="margin: 10px 0 0 0;">如果您沒有申請密碼重設，請忽略此郵件。您的帳號仍然安全，密碼不會被更改。</p>
                </div>
            </div>
            <div class="footer">
                <p style="margin: 0;">© 2025 Accounting System. All rights reserved.</p>
                <p style="margin: 5px 0 0 0;">此為系統自動發送的郵件，請勿直接回覆。</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(
        to_email=to_email,
        subject="密碼重設請求 - Accounting System",
        html_content=html_content
    )
