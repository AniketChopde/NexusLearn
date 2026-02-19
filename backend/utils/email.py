from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List, Dict, Any
from pathlib import Path
from loguru import logger
import os

from config import settings

class EmailSchema(BaseModel):
    email: List[EmailStr]

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=settings.mail_starttls,
    MAIL_SSL_TLS=settings.mail_ssl_tls,
    USE_CREDENTIALS=settings.use_credentials,
    VALIDATE_CERTS=True
)

class EmailService:
    def __init__(self):
        self.fastmail = FastMail(conf)

    async def send_reset_password_email(self, email: EmailStr, token: str, host_url: str):
        """
        Send a password reset email to the user.
        """
        try:
            reset_link = f"{host_url}/reset-password?token={token}"
            
            html = f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Hello,</p>
                    <p>You have requested to reset your password. Please click the link below to reset it:</p>
                    <p><a href="{reset_link}">Reset Password</a></p>
                    <p>If you did not request this, please ignore this email.</p>
                    <p>The link will expire in 30 minutes.</p>
                    <br>
                    <p>Best regards,</p>
                    <p>{settings.app_name} Team</p>
                </body>
            </html>
            """

            message = MessageSchema(
                subject=f"{settings.app_name} - Password Reset",
                recipients=[email],
                body=html,
                subtype=MessageType.html
            )

            await self.fastmail.send_message(message)
            logger.info(f"Password reset email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {str(e)}")
            # In development, we might not have a valid SMTP server, so we log the link
            if settings.debug:
                logger.warning(f"DEBUG MODE - Reset Link: {reset_link}")
                return True # Pretend success in debug
            return False
