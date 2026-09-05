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

    @classmethod
    async def send_severe_weather_alert_email(cls, recipient_email: str, user_name: str, location_name: str, smart_alert_dict: dict):
        """Sends an immediate severe weather risk emergency email alert."""
        risk_score = smart_alert_dict.get("risk_score", 85)
        risk_level = smart_alert_dict.get("risk_level", "Severe Risk")
        event_desc = smart_alert_dict.get("event_description", "Extreme weather detected")
        safety_advice = smart_alert_dict.get("safety_advice", "Stay indoors immediately.")
        travel_warning = smart_alert_dict.get("travel_warning", "Do not travel.")
        hazards = smart_alert_dict.get("detected_hazards", [])

        subject = f"🚨 EMERGENCY WEATHER ALERT ({risk_score}% Risk): {location_name}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
            .card {{ max-width: 580px; margin: 0 auto; background: #1e293b; border-radius: 20px; padding: 30px; border: 2px solid #ef4444; box-shadow: 0 10px 30px rgba(239, 68, 68, 0.4); }}
            .logo {{ font-size: 24px; font-weight: 800; color: #ef4444; text-align: center; margin-bottom: 10px; }}
            .alert-banner {{ background: #7f1d1d; border: 1px solid #ef4444; color: #fecaca; font-size: 14px; font-weight: 800; padding: 12px; border-radius: 12px; text-align: center; margin: 15px 0; }}
            .risk-score {{ font-size: 48px; font-weight: 900; color: #ef4444; text-align: center; margin: 10px 0; }}
            .box {{ background: #0f172a; padding: 15px; border-radius: 12px; border: 1px solid #334155; margin: 12px 0; font-size: 13px; color: #cbd5e1; }}
            .footer {{ font-size: 12px; color: #94a3b8; text-align: center; margin-top: 30px; border-top: 1px solid #334155; padding-top: 15px; }}
          </style>
        </head>
        <body>
          <div class="card">
            <div class="logo">🚨 WeatherGPT Emergency Alert</div>
            <div class="alert-banner">CRITICAL WEATHER HAZARD DETECTED FOR {location_name.upper()}</div>
            
            <div class="risk-score">{risk_score}% RISK</div>
            <p style="text-align:center; font-weight:700; color:#ef4444;">Level: {risk_level}</p>

            <h3>Hello {user_name},</h3>
            <p>Our live WeatherGPT Smart Safety System detected severe risk weather conditions in <strong>{location_name}</strong>:</p>

            <div class="box">
              <strong>⚠️ Active Hazards:</strong> {', '.join(hazards) if hazards else 'Extreme severe weather'}
              <br/><br/>
              <strong>ℹ️ What is happening:</strong> {event_desc}
            </div>

            <div class="box" style="border-color: #ef4444; background: #450a0a;">
              <strong>🛡️ Recommended Safety Steps:</strong>
              <p style="margin-top: 5px; color: #fecaca;">{safety_advice}</p>
            </div>

            <div class="box" style="border-color: #f59e0b; background: #451a03;">
              <strong>🚗 Travel Status:</strong>
              <p style="margin-top: 5px; color: #fef08a;">{travel_warning}</p>
            </div>

            <div class="footer">
              © 2026 WeatherGPT — Conversational Voice-First Weather Intelligence Platform
            </div>
          </div>
        </body>
        </html>
        """

        print("\n" + "="*60)
        print(f"  🚨 EMERGENCY SEVERE WEATHER EMAIL DISPATCHED TO {recipient_email}")
        print(f"  Location: {location_name} | Risk: {risk_score}% ({risk_level})")
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
                logger.info(f"Successfully sent severe weather email alert to {recipient_email}")
            except Exception as e:
                logger.error(f"Failed to send severe weather email alert via SMTP ({e}).")


