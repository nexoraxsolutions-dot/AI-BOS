import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("ai_bos")


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> bool:
    """Send an email via SMTP. Falls back to logging in development."""
    if not settings.smtp_host or settings.smtp_host == "localhost":
        # Development mode: log the email instead of sending
        logger.info(
            "DEV EMAIL [To: %s] [Subject: %s]\n%s",
            to_email,
            subject,
            html_content,
        )
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.email_from_name} <{settings.email_from_address}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        if text_content:
            msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.email_from_address, [to_email], msg.as_string())

        logger.info("Email sent successfully to %s", to_email)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        return False


async def send_verification_email(to_email: str, token: str) -> bool:
    """Send an email verification link to the user."""
    verification_url = f"{settings.frontend_url}/verify-email?token={token}"
    subject = "Verify your email address - AI-BOS"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                       color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
            .button {{ display: inline-block; padding: 12px 30px; background: #667eea;
                       color: white; text-decoration: none; border-radius: 5px;
                       font-weight: bold; margin: 20px 0; }}
            .footer {{ margin-top: 20px; font-size: 12px; color: #999; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to AI-BOS!</h1>
            </div>
            <div class="content">
                <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
                <p style="text-align: center;">
                    <a class="button" href="{verification_url}">Verify Email Address</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; font-size: 12px; color: #667eea;">{verification_url}</p>
                <p>This link will expire in {settings.email_verification_token_expire_hours} hours.</p>
                <p>If you did not create an account, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 AI-BOS. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
Welcome to AI-BOS!

Thank you for registering. Please verify your email address by clicking the link below:

{verification_url}

This link will expire in {settings.email_verification_token_expire_hours} hours.

If you did not create an account, please ignore this email.
    """

    return await send_email(to_email, subject, html_content, text_content)