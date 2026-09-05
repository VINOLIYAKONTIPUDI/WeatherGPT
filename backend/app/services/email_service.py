import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    @classmethod
    async def send_otp_email(cls, recipient_email: str, otp: str, user_name: str = "User"):
        """Sends 6-digit verification OTP email to user."""
        subject = f"Your WeatherGPT Verification Code: {otp}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .card {{ max-width: 500px; margin: 0 auto; background: #1e293b; border-radius: 20px; padding: 30px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            .logo {{ font-size: 24px; font-weight: 800; color: #38bdf8; text-align: center; margin-bottom: 20px; }}
            .otp-box {{ font-size: 36px; font-weight: 900; letter-spacing: 8px; color: #38bdf8; background: #0f172a; padding: 15px; border-radius: 12px; text-align: center; margin: 25px 0; border: 1px solid #0284c7; }}
            .footer {{ font-size: 12px; color: #94a3b8; text-align: center; margin-top: 30px; border-top: 1px solid #334155; padding-top: 15px; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="logo">🌦️ WeatherGPT</div>
            <h2>Hello {user_name},</h2>
            <p>Thank you for registering with WeatherGPT. Please use the following 6-digit OTP code to verify your email address:</p>
            
            <div class="otp-box">{otp}</div>
            
            <p>⏱️ This OTP code is valid for <strong>5 minutes</strong>. If you did not request this code, please ignore this email.</p>
            
            <div class="footer">
              © 2026 WeatherGPT — Conversational Voice-First Weather Intelligence Platform
            </div>
          </div>
        </body>
        </html>
        """

        # Log OTP prominently in console for verification & testing
        logger.info(f"[EmailService] VERIFICATION OTP FOR {recipient_email}: [{otp}] (Expires in 5 minutes)")
        try:
            print("\n" + "="*60)
            print(f"  VERIFICATION OTP FOR {recipient_email}: [{otp}] (Expires in 5 minutes)")
            print("="*60 + "\n")
        except Exception:
            pass

        # If SMTP server credentials are provided, send live email
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD and settings.SMTP_SERVER:
            try:
                def send_mail():
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"] = settings.EMAIL_FROM or settings.SMTP_USERNAME
                    msg["To"] = recipient_email
                    
                    part = MIMEText(html_content, "html")
                    msg.attach(part)
                    
                    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                        server.starttls()
                        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                        server.sendmail(msg["From"], recipient_email, msg.as_string())

                # Run blocking SMTP send in threadpool executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, send_mail)
                logger.info(f"Successfully sent OTP email to {recipient_email}")
            except Exception as e:
                logger.error(f"Failed to send email via SMTP ({e}). OTP code [{otp}] logged to server console.")
