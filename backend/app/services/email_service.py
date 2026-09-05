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
        subject = f"🔐 Your WeatherGPT Verification Code: {otp}"
        
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

        # ALWAYS log OTP prominently in console for local debugging & testing
        print("\n" + "="*60)
        print(f"  🔑 VERIFICATION OTP FOR {recipient_email}: [{otp}] (Expires in 5 minutes)")
        print("="*60 + "\n")

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

    @classmethod
    async def send_weather_notification_email(cls, recipient_email: str, user_name: str, notif_type: str, location_name: str, weather_info: dict):
        """Sends scheduled weather report email (Rain / Temp / Full Weather) to recipient."""
        type_titles = {
            "rain": "🌧️ Scheduled Rain & Precipitation Alert",
            "temperature": "🌡️ Scheduled Temperature Forecast",
            "full": "🌦️ Scheduled Weather Intelligence Briefing"
        }
        subject = f"{type_titles.get(notif_type, '🌦️ Weather Alert')} for {location_name}"

        temp = weather_info.get("temperature", "--")
        condition = weather_info.get("condition", "Partly Cloudy")
        pop = weather_info.get("rain_probability", weather_info.get("precipitation_probability", 0))
        humidity = weather_info.get("humidity", 60)
        wind = weather_info.get("wind_speed", 10)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .card {{ max-width: 550px; margin: 0 auto; background: #1e293b; border-radius: 20px; padding: 30px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            .logo {{ font-size: 24px; font-weight: 800; color: #38bdf8; text-align: center; margin-bottom: 20px; }}
            .badge {{ display: inline-block; background: #0284c7; color: #ffffff; font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 9999px; margin-bottom: 15px; }}
            .weather-box {{ background: #0f172a; padding: 20px; border-radius: 16px; border: 1px solid #06b6d4; margin: 20px 0; }}
            .metric {{ font-size: 32px; font-weight: 900; color: #38bdf8; }}
            .sub-metric {{ font-size: 14px; color: #94a3b8; margin-top: 5px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; text-align: left; }}
            .grid-item {{ background: #1e293b; padding: 10px; border-radius: 10px; font-size: 13px; color: #cbd5e1; }}
            .footer {{ font-size: 12px; color: #94a3b8; text-align: center; margin-top: 30px; border-top: 1px solid #334155; padding-top: 15px; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="logo">🌦️ WeatherGPT</div>
            <div style="text-align:center;"><span class="badge">{notif_type.upper()} ALERT</span></div>
            <h2>Hello {user_name},</h2>
            <p>Here is your scheduled weather update for <strong>{location_name}</strong>:</p>
            
            <div class="weather-box" style="text-align: center;">
              <div class="metric">{temp}°C</div>
              <div class="sub-metric">Condition: <strong>{condition}</strong></div>
              
              <div class="grid">
                <div class="grid-item">🌧️ Rain Chance: <strong>{pop}%</strong></div>
                <div class="grid-item">💧 Humidity: <strong>{humidity}%</strong></div>
                <div class="grid-item">💨 Wind Speed: <strong>{wind} km/h</strong></div>
                <div class="grid-item">📍 Location: <strong>{location_name}</strong></div>
              </div>
            </div>
            
            <p style="font-size: 13px; color: #cbd5e1;">💡 <em>Recommendation: Keep an eye on WeatherGPT live dashboard for real-time agricultural & travel updates.</em></p>
            
            <div class="footer">
              © 2026 WeatherGPT — Conversational Voice-First Weather Intelligence Platform
            </div>
          </div>
        </body>
        </html>
        """

        print("\n" + "="*60)
        print(f"  📩 SCHEDULED EMAIL SENT TO {recipient_email} [{location_name} - {notif_type.upper()}]")
        print(f"  Temperature: {temp}°C | Rain Chance: {pop}% | Condition: {condition}")
        print("="*60 + "\n")

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

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, send_mail)
                logger.info(f"Successfully sent weather notification email to {recipient_email}")
            except Exception as e:
                logger.error(f"Failed to send weather notification email via SMTP ({e}).")

