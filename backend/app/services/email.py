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
        # SECURITY: Redact any tokens/URLs from logs to prevent accidental exposure
        safe_html = html_content.replace("?token=", "?token=[REDACTED]")
        safe_text = text_content.replace("?token=", "?token=[REDACTED]") if text_content else None
        logger.info(
            "DEV EMAIL [To: %s] [Subject: %s]\nHTML:\n%s\nText:\n%s",
            to_email,
            subject,
            safe_html,
            safe_text,
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


async def send_password_reset_email(
    to_email: str,
    token: str,
    frontend_url: str,
    company_name: str = "AI-BOS",
    company_logo_url: str | None = None,
    support_email: str | None = None,
    expiry_hours: int = 1,
) -> bool:
    """
    Send a password reset email with professional template.

    Args:
        to_email: Recipient email address
        token: Password reset token (will be included in reset URL)
        frontend_url: Base URL of the frontend application
        company_name: Company name for branding
        company_logo_url: Optional company logo URL
        support_email: Optional support email address
        expiry_hours: Token expiration time in hours

    Returns:
        True if email was queued/sent successfully, False otherwise

    Security:
        - Token is never logged or exposed in plain text
        - Uses HTTPS reset links
        - Includes expiration notice
        - Includes ignore message for unauthorized requests
    """
    reset_url = f"{frontend_url}/reset-password?token={token}"
    subject = f"Password Reset - {company_name}"

    # Support email defaults to from address if not provided
    if not support_email:
        from app.core.config import settings
        support_email = settings.email_from_address

    # Company logo HTML (if provided)
    logo_html = ""
    if company_logo_url:
        logo_html = f'<img src="{company_logo_url}" alt="{company_name}" style="max-height: 60px; margin-bottom: 20px;" />'

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .email-wrapper {{ background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; }}
            .header h1 {{ margin: 10px 0 0 0; font-size: 28px; font-weight: 600; }}
            .content {{ background: #ffffff; padding: 40px 30px; }}
            .button {{ display: inline-block; padding: 14px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 25px 0; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .button:hover {{ opacity: 0.9; }}
            .link-box {{ background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 15px; margin: 20px 0; word-break: break-all; font-size: 13px; color: #667eea; }}
            .warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }}
            .info {{ background-color: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin: 20px 0; border-radius: 4px; }}
            .footer {{ background-color: #f8f9fa; padding: 20px 30px; text-align: center; font-size: 12px; color: #6c757d; border-top: 1px solid #dee2e6; }}
            .footer a {{ color: #667eea; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="email-wrapper">
                <div class="header">
                    {logo_html}
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>We received a request to reset your password for your <strong>{company_name}</strong> account.</p>

                    <p style="text-align: center;">
                        <a class="button" href="{reset_url}">Reset Password</a>
                    </p>

                    <p><strong>This link will expire in {expiry_hours} hour(s).</strong></p>

                    <div class="info">
                        <p style="margin: 0;"><strong>Having trouble clicking the button?</strong></p>
                        <p style="margin: 5px 0 0 0;">Copy and paste this link into your browser:</p>
                    </div>
                    <div class="link-box">{reset_url}</div>

                    <div class="warning">
                        <p style="margin: 0;"><strong>Didn't request this?</strong></p>
                        <p style="margin: 5px 0 0 0;">If you did not request a password reset, please ignore this email. Your account remains secure and no changes have been made.</p>
                    </div>

                    <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 14px; color: #6c757d;">
                        For security reasons, this link can only be used once and will expire after {expiry_hours} hour(s).
                    </p>
                </div>
                <div class="footer">
                    <p style="margin: 0 0 10px 0;">&copy; 2026 {company_name}. All rights reserved.</p>
                    <p style="margin: 0; font-size: 11px;">
                        Need help? Contact us at <a href="mailto:{support_email}">{support_email}</a>
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
Password Reset - {company_name}

We received a request to reset your password for your {company_name} account.

Click the link below to set a new password:

{reset_url}

This link will expire in {expiry_hours} hour(s).

If you did not request a password reset, please ignore this email. Your account remains secure and no changes have been made.

For security reasons, this link can only be used once and will expire after {expiry_hours} hour(s).

Need help? Contact us at {support_email}

© 2026 {company_name}. All rights reserved.
    """

    return await send_email(to_email, subject, html_content, text_content)


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


async def send_invitation_email(
    to_email: str,
    token: str,
    company_name: str,
    inviter_name: Optional[str] = None,
    role: Optional[str] = None,
) -> bool:
    """Send a company invitation link to a user."""
    invite_url = f"{settings.frontend_url}/invitations/accept?token={token}"
    inviter = inviter_name or "An administrator"
    role_text = f" as {role}" if role else ""
    subject = f"You've been invited to join {company_name}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin:0; padding:20px;">
        <div style="max-width:600px;margin:0 auto;">
            <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:30px;text-align:center;border-radius:8px 8px 0 0;">
                <h1 style="margin:0;">You're invited!</h1>
            </div>
            <div style="background:#f9f9f9;padding:30px;border-radius:0 0 8px 8px;">
                <p>Hi,</p>
                <p><strong>{inviter}</strong> has invited you to join <strong>{company_name}</strong>{role_text} on AI-BOS.</p>
                <p style="text-align:center;">
                    <a href="{invite_url}" style="display:inline-block;padding:12px 30px;background:#667eea;color:white;text-decoration:none;border-radius:5px;font-weight:bold;margin:20px 0;">
                        Accept Invitation
                    </a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break:break-all;font-size:12px;color:#667eea;">{invite_url}</p>
                <p>This invitation will expire in {settings.company_invitation_expire_hours} hours.</p>
                <p>If you were not expecting this invitation, you can safely ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    text_content = f"""
You've been invited to join {company_name} on AI-BOS.

{inviter} has invited you{role_text}.

Accept the invitation here:
{invite_url}

This invitation expires in {settings.company_invitation_expire_hours} hours.

If you were not expecting this invitation, you can safely ignore this email.
"""
    return await send_email(to_email, subject, html_content, text_content)