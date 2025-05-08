import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables from .env file
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(to_email, subject, html_content):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print("❌ Email send error:", e)
        raise


def send_welcome_email(user_email, user_name):
    subject = "Welcome to JefJet Flight Bookings!"
    body = f"""
    <h2>Hi {user_name.title()},</h2>
    <p>Thank you for registering at <strong>JefJet Flight Bookings</strong>.</p>
    <p>You can now log in and start booking your flights.</p>
    <br>
    <p>Safe travels,<br>JefJet Team</p>
    """
    send_email(user_email, subject, body)
