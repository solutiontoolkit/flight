from datetime import datetime
import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template
from flask_mail import Mail, Message
from database.db import get_db_connection
from database import db
from extensions import mail

import base64
import qrcode

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO



def get_base64_logo():
    logo_path = os.path.join("static", "img", "jet_logo.jpg")
    with open(logo_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


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
            <img src="static/img/jet_logo.jpg" alt="JefJet Logo" style="height: 60px;" />
        </div>
        <h2 style="color: #333;">Hi {user_name.title()},</h2>
        <p>Thank you for registering at <strong>JefJet Flight Bookings</strong>.</p>
        <p>You can now log in and start booking your flights with ease.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="https://flight-8oui.onrender.com/booking" style="
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

def send_booking_confirmation_email(user_email, user_name, booking, is_paid=False):
    subject = f"Booking Confirmation - JefJet Flight #{booking['id']}"
    payment_status = "PAID ✅" if is_paid else "UNPAID ❌"

    # ✅ Load logo before using it
    logo_64 = get_base64_logo()

    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; border-radius: 8px; padding: 20px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/jpeg;base64,{logo_64}" alt="JefJet Logo" style="height: 60px;" />
            <h2 style="color: #333;">JefJet Flight Booking Confirmation</h2>
            <p style="font-size: 16px;">Booking ID: <strong>{booking['id']}</strong> | Status: <strong>{payment_status}</strong></p>
        </div>
        <h3 style="color: #333;">Passenger Information:</h3>
        <ul>
            <li><strong>Name:</strong> {user_name.title()}</li>
            <li><strong>Email:</strong> {user_email}</li>
            <li><strong>NIN:</strong> {booking['nin']}</li>
        </ul>
        <h3 style="color: #333;">Flight Details:</h3>
        <ul>
            <li><strong>Departure:</strong> {booking['from_location']}</li>
            <li><strong>Destination:</strong> {booking['to_location']}</li>
            <li><strong>Date:</strong> {booking['depart_date']}</li>
        </ul>
        <p style="margin-top: 30px; color: #555;">Thank you for choosing <strong>JefJet</strong>. Safe travels!</p>
    </div>
    """

    print(f"Sending booking email to {user_email} for booking ID {booking['id']}")
    send_email(user_email, subject, body)


def send_email_notification(user_id, booking_id, action_type):
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

        msg = Message(subject=subject,
                      recipients=[user['email']],
                      html=body,
                      sender=current_app.config['MAIL_USERNAME'])

        mail = Mail(current_app)
        mail.send(msg)

    except Exception as e:
        print(f"Error sending email: {e}")
    finally:
        cursor.close()
        conn.close()


    

def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode("utf-8")

def send_payment_confirmation_email(user, booking, pdf_path):
    try:
        if not user or 'email' not in user:
            print("❌ No valid user email provided.")
            return

        if not os.path.exists(pdf_path):
            print(f"❌ PDF not found at: {pdf_path}")
            return

        print(f"📤 Preparing to send payment confirmation email to {user['email']}")

        # Load and encode logo image
        logo_b64 = get_base64_image("static/img/jet_logo.jpg")

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
            <div style="text-align: center;">
                <img src="data:image/jpeg;base64,{logo_b64}" alt="Logo" style="height: 60px;" />
                <h2>Payment Confirmation</h2>
            </div>
            <p>Dear {user['name'].title()},</p>
            <p>We have received your payment for the booking <strong>#{booking['id']}</strong>.</p>
            <p>Attached is your official booking receipt.</p>
            <p>Thank you for flying with <strong>JefJet</strong>.</p>
        </div>
        """

        msg = MIMEMultipart()
        sender = current_app.config.get('MAIL_USERNAME') or os.getenv('EMAIL_ADDRESS')
        password = current_app.config.get('MAIL_PASSWORD') or os.getenv('EMAIL_PASSWORD')
        smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = int(current_app.config.get('MAIL_PORT', 465))

        msg['From'] = sender
        msg['To'] = user['email']
        msg['Subject'] = f"Payment Confirmation - Booking #{booking['id']}"
        msg.attach(MIMEText(html_content, 'html'))

        with open(pdf_path, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename=payment_confirmation_{booking["id"]}.pdf')
            msg.attach(part)

        print(f"📡 Connecting to SMTP server {smtp_server}:{smtp_port}...")
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
            smtp.set_debuglevel(1)
            smtp.login(sender, password)
            smtp.send_message(msg)
            print(f"✅ Payment confirmation email sent to {user['email']}")

    except Exception as e:
        print(f"❌ Failed to send payment confirmation email: {e}")





def generate_qr_code_for_payment(booking):
    payment_url = f"https://payment-url.com/{booking['id']}/paid"
    qr_code = qrcode.make(payment_url)
    qr_code_path = f"./static/qrcodes/payment_qr_{booking['id']}.png"
    qr_code.save(qr_code_path)
    return qr_code_path




def generate_booking_slip_pdf(booking, pdf_path):
    """
    Generate a booking slip PDF with booking info and save it to pdf_path.
    
    booking: dict containing booking and user info, e.g.
      {
        'id': 123,
        'trip_type': 'One-way',
        'from_location': 'Lagos',
        'to_location': 'Abuja',
        'depart_date': '2025-06-01',
        'return_date': None,
        'adults': 2,
        'children': 1,
        'infants': 0,
        'class_of_travel': 'Economy',
        'airline_name': 'JefJet Airlines',
        'name': 'Joshua',
        'email': 'joshua@example.com',
        'nin': '1234567890',
        'payment_status': 'paid'  # optional
      }
    pdf_path: str path to save the PDF file
    """

    # Create QR code data string - could be booking reference and user email
    qr_data = f"Booking Reference: JEF-{booking['id']}\nPassenger: {booking.get('name', 'N/A')}\nEmail: {booking.get('email', 'N/A')}"
    qr_img = qrcode.make(qr_data)
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_image = ImageReader(qr_buffer)

    # Create PDF canvas
    c = canvas.Canvas(pdf_path, pagesize=letter)

    # Header
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, 750, "JEFJET Booking")

    c.setFont("Helvetica", 10)
    c.drawString(50, 735, "P.O Box 4. PTI Road Uvwie City, Delta-Nigeria")
    c.drawString(50, 720, "Phone: (123) 456-7890")
    c.drawString(50, 705, "Email: mukorojeffreyoghenevwegba.com")
    c.line(50, 700, 550, 700)

    # Booking Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 680, "Customer's Booking Slip")

    # Booking Info Text
    y = 660
    info_lines = [
        f"Booking Reference: JEF-{booking['id']}",
        f"Trip Type: {booking.get('trip_type', 'N/A')}",
        f"From: {booking.get('from_location', 'N/A')}",
        f"To: {booking.get('to_location', 'N/A')}",
        f"Departure Date: {booking.get('depart_date', 'N/A')}",
        f"Return Date: {booking.get('return_date', 'N/A') or 'N/A'}",
        f"Adults: {booking.get('adults', 0)}",
        f"Children: {booking.get('children', 0)}",
        f"Infants: {booking.get('infants', 0)}",
        f"Class: {booking.get('class_of_travel', 'N/A')}",
        f"Airline: {booking.get('airline_name', 'N/A')}",
        f"Passenger Name: {booking.get('name', 'N/A')}",
        f"Email: {booking.get('email', 'N/A')}",
        f"NIN: {booking.get('nin', 'N/A')}",
    ]
    # Optionally include payment status if exists
    if 'payment_status' in booking:
        info_lines.append(f"Payment Status: {booking['payment_status'].title()}")

    for line in info_lines:
        c.setFont("Helvetica", 12)
        c.drawString(50, y, line)
        y -= 18  # line spacing

    # Draw QR code bottom right
    c.drawImage(qr_image, 400, 550, width=150, height=150)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(400, 540, "Scan this code to view your booking details")

    c.showPage()
    c.save()

def send_flight_reminder_email(user, booking, flight_type="departure"):
    try:
        msg = MIMEMultipart()
        msg['From'] = current_app.config.get('MAIL_USERNAME')
        msg['To'] = user['email']
        msg['Subject'] = f"Reminder: Your {flight_type.capitalize()} Flight is Tomorrow"

        html = f"""
        <p>Hi {user['name'].title()},</p>
        <p>This is a reminder that your <strong>{flight_type}</strong> flight is scheduled for tomorrow.</p>
        <p>Booking ID: {booking['id']}</p>
        <p>Thank you for choosing <strong>JefJet</strong>.</p>
        """

        msg.attach(MIMEText(html, 'html'))

        print("📡 Connecting to SMTP server for reminder...")
        with smtplib.SMTP_SSL(current_app.config.get('MAIL_SERVER'), int(current_app.config.get('MAIL_PORT'))) as smtp:
            smtp.login(current_app.config.get('MAIL_USERNAME'), current_app.config.get('MAIL_PASSWORD'))
            smtp.send_message(msg)
            print(f"✅ Reminder email sent to {user['email']} for {flight_type} flight")

    except Exception as e:
        import traceback
        print("❌ Error sending reminder email:")
        traceback.print_exc()



def get_base64_image(img_path):
    if not os.path.exists(img_path):
        return ''
    with open(img_path, 'rb') as image_file:
        return b64encode(image_file.read()).decode('utf-8')

def send_payment_confirmation_email(user, booking, pdf_path):
    try:
        print(f"Preparing to send payment confirmation email to {user['email']}")
        print("Checking PDF existence:", os.path.exists(pdf_path))

        logo_b64 = get_base64_image("static/img/jet_logo.jpg")
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
            <div style="text-align: center;">
                <img src="data:image/jpeg;base64,{logo_b64}" alt="Logo" style="height: 60px;" />
                <h2>Payment Confirmation</h2>
            </div>
            <p>Dear {user['name'].title()},</p>
            <p>We have received your payment for the booking <strong>#{booking['id']}</strong>.</p>
            <p>Attached is your official booking receipt.</p>
            <p>Thank you for flying with <strong>JefJet</strong>.</p>
        </div>
        """

        msg = MIMEMultipart()
        msg['From'] = current_app.config.get('MAIL_USERNAME')
        msg['To'] = user['email']
        msg['Subject'] = f"Payment Confirmation - Booking #{booking['id']}"
        msg.attach(MIMEText(html_content, 'html'))

        with open(pdf_path, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename=payment_confirmation_{booking['id']}.pdf")

            msg.attach(part)

        print("📡 Connecting to SMTP server...")
        with smtplib.SMTP_SSL(current_app.config.get('MAIL_SERVER'), int(current_app.config.get('MAIL_PORT'))) as smtp:
            smtp.login(current_app.config.get('MAIL_USERNAME'), current_app.config.get('MAIL_PASSWORD'))
            print("✅ SMTP login successful.")
            smtp.send_message(msg)
            print("✅ Payment confirmation email sent to", user['email'])

    except Exception as e:
        import traceback
        print("❌ Exception during sending payment email:")
        traceback.print_exc()


'''
def send_flight_reminder_email(user, booking, flight_type="departure"):
   
    subject = f"Flight Reminder: Your {flight_type.title()} Flight is Tomorrow!"
    flight_date = booking['depart_date'] if flight_type == "departure" else booking['return_date']

    msg = Message(subject, recipients=[user['email']])
    msg.body = f"""
Hi {user.get('name', 'Traveler')},

This is a friendly reminder that your {flight_type} flight is scheduled for:

📍 From: {booking['from_location']}
📍 To: {booking['to_location']}
📅 Date: {flight_date}
✈ Airline: {booking.get('airline_name', 'N/A')}
🪑 Class: {booking.get('class_of_travel', 'N/A')}

Booking ID: {booking.get('id')}

Please arrive at the airport 2–3 hours before departure.

Safe travels!
— JEFJET Flights Team
"""
    print("Sending reminder for booking:", booking['id'], "to user:", user['email'])

    mail.send(msg)
'''
