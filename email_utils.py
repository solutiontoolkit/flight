import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_mail import Message
from flask import current_app, render_template
from flask_mail import Mail

from database.db import get_db_connection

# Load environment variables from .env file
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(to_email, subject, html_content):
    print(f"📝 Preparing to send email to {to_email}...")  # Debug: Check if the email parameters are correct.
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_content, 'html'))

    try:
        print("📧 Attempting to send email via Gmail SMTP...")
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
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; border-radius: 8px; padding: 20px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://i.imgur.com/F6V1U6Y.png" alt="JefJet Logo" style="height: 60px;" />
        </div>
        <h2 style="color: #333;">Hi {user_name.title()},</h2>
        <p>Thank you for registering at <strong>JefJet Flight Bookings</strong>.</p>
        <p>You can now log in and start booking your flights with ease.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="http://localhost:5000/booking" style="
                background-color: #007BFF;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;">
                Proceed to Booking
            </a>
        </div>
        <p style="color: #555;">Safe travels,<br><strong>JefJet Team</strong></p>
    </div>
    """
    send_email(user_email, subject, body)



 

def send_email_notification(user_id, booking_id, action_type):
    # Assuming the Mail extension is initialized
    mail = Mail()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT email, name FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return "User not found"

        if action_type == "cancellation":
            subject = f"Your booking (ID: {booking_id}) has been cancelled"
            body = render_template('email/cancellation_email.html', user=user, booking_id=booking_id)
        
        # Send email (using flask_mail's Message class)
        msg = Message(subject=subject,
                      recipients=[user['email']],
                      html=body)
        mail.send(msg)
    
    except Exception as e:
        print(f"Error sending email: {e}")
    finally:
        cursor.close()
        conn.close()

    
    
    import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import current_app

def send_payment_confirmation_email(user_id, booking, pdf_path):
    # Fetch user details (email, name, etc.)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        sender_email = current_app.config['MAIL_USERNAME']
        receiver_email = user['email']
        password = current_app.config['MAIL_PASSWORD']

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = "Payment Confirmation for Your Booking"

        body = f"Dear {user['name']},\n\nYour booking with JEFJET has been successfully paid. Please find the payment confirmation PDF attached.\n\nThank you for choosing JEFJET!"
        msg.attach(MIMEText(body, 'plain'))

        # Attach PDF
        attachment = open(pdf_path, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename=payment_confirmation_{booking['id']}.pdf")
        msg.attach(part)

        # Send the email
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
            server.quit()
        except Exception as e:
            print(f"Error sending email: {e}")

import qrcode

def generate_qr_code_for_payment(booking):
    payment_url = f"https://payment-url.com/{booking['id']}/paid"
    qr_code = qrcode.make(payment_url)
    qr_code_path = f"./static/qrcodes/payment_qr_{booking['id']}.png"
    qr_code.save(qr_code_path)
    return qr_code_path
