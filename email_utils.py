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
            <img src="static/img/jet_logo.jpg" alt="JefJet Logo" style="height: 60px;" />
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

def send_booking_confirmation_email(user_email, user_name, booking, is_paid=False):
    subject = f"Booking Confirmation - JefJet Flight #{booking['id']}"
    payment_status = "PAID ✅" if is_paid else "UNPAID ❌"
    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; border-radius: 8px; padding: 20px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://i.imgur.com/F6V1U6Y.png" alt="JefJet Logo" style="height: 60px;" />
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
            <li><strong>Departure:</strong> {booking['departure']}</li>
            <li><strong>Destination:</strong> {booking['destination']}</li>
            <li><strong>Date:</strong> {booking['date']}</li>
        </ul>
        <p style="margin-top: 30px; color: #555;">Thank you for choosing <strong>JefJet</strong>. Safe travels!</p>
    </div>
    """
    send_email(user_email, subject, body)

from flask_mail import Message
from flask import current_app
from flask_mail import Mail

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


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import qrcode
from reportlab.lib.utils import ImageReader

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


