import base64
from multiprocessing.resource_tracker import getfd
from flask import Flask, render_template, redirect, url_for, session, request, flash, make_response
from flask_mail import Mail, Message
from xhtml2pdf import pisa
from io import BytesIO
import bcrypt
import os
import database.db
from dotenv import load_dotenv
import qrcode
import io
from flask import send_file
from flask import render_template_string
from database.db import get_user_by_email
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.message import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from database import db



# Import modules
from database.db import get_db_connection
from database.db import get_user_by_email
from email_utils import send_email, send_payment_confirmation_email, send_welcome_email
from social_auth import google_bp, facebook_bp, linkedin_bp, handle_social_login
from flask_dance.contrib.google import google
from flask_dance.contrib.facebook import facebook
from flask_dance.contrib.linkedin import linkedin
from itsdangerous import URLSafeTimedSerializer as Serializer, BadSignature, SignatureExpired


# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_ADDRESS")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)

# Secret key for session management
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')

# Register social login blueprints
app.register_blueprint(google_bp, url_prefix="/login")
app.register_blueprint(facebook_bp, url_prefix="/login")
app.register_blueprint(linkedin_bp, url_prefix="/login")


# --- Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/account')
def account():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('account'))  # Redirect to login if not logged in

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch user info
        cursor.execute("SELECT id, name, email, nin FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        # Fetch bookings for user
        cursor.execute("""
            SELECT 
                id, trip_type, from_location, to_location,
                depart_date, return_date, adults, children, infants,
                class_of_travel, airline_name, created_at
            FROM bookings
            WHERE user_id = %s
            ORDER BY id DESC
        """, (user_id,))
        bookings = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    if user:
        return render_template('dashboard.html', user=user, bookings=bookings)
    else:
        return "User not found"
    
    


@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'user_id' not in session:
        return redirect(url_for('account'))
    return render_template('bookin.html')

@app.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
def payment(booking_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('account'))

    # Check the booking exists and belongs to the user
    booking = db.get_booking(booking_id, user_id)
    if not booking:
        flash('Invalid booking or unauthorized access.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Simulate saving payment info (in real you would process card)
        card_number = request.form.get('card_number')
        expiry = request.form.get('expiry')
        cvv = request.form.get('cvv')

        if card_number and expiry and cvv:
            # Mark booking as paid in your database
            db.mark_booking_paid(booking_id)

            # Flash message
            flash('Payment successful! Your receipt is ready.', 'success')

            # Redirect to payment success page
            return redirect(url_for('payment_success', booking_id=booking_id))
        else:
            flash('Please fill all payment details.', 'danger')

    return render_template('payment.html', booking=booking)






@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name'].upper()
    email = request.form['email']
    password = request.form['password']
    nin = request.form['NIN']
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, email, password, nin) VALUES (%s, %s, %s, %s)", 
                       (name, email, hashed, nin))
        conn.commit()

        try:
            send_welcome_email(email, name)
        except Exception as e:
            print("Email error:", e)
            flash("Registered successfully, but email not sent.", "warning")
        else:
            flash("Registration successful! Welcome email sent.", "success")

    except Exception as e:
        print("Signup error:", e)
        flash("Signup failed: " + str(e), "danger")
        return redirect(url_for('show_signin'))
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('show_signin'))

@app.route('/signin', methods=['POST'])
def signin():
    identifier = request.form['identifier']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s OR nin = %s", (identifier, identifier))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        session['user_id'] = user['id']
        flash('You have successfully logged In!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid email/NIN or password. Please try again.', 'danger')
        return render_template('login.html')

@app.route('/signin', methods=['GET'])
def show_signin():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('account'))




@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    if 'user_id' not in session:
        return redirect(url_for('account'))

    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO bookings (
                user_id, trip_type, from_location, to_location,
                depart_date, return_date, adults, children, infants,
                class_of_travel, airline_name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session['user_id'],
            data.get('trip_type'),
            data.get('from_location'),
            data.get('to_location'),
            data.get('depart_date'),
            data.get('return_date'),
            data.get('adults'),
            data.get('children'),
            data.get('infants'),
            data.get('class_of_travel'),
            data.get('airline_name')
        ))
        conn.commit()
        booking_id = cursor.lastrowid
    except Exception as e:
        print("Booking error:", e)
        return "Booking submission failed: " + str(e)
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('booking_confirmation', booking_id=booking_id))



from flask import send_file
import qrcode
import base64
from datetime import datetime

@app.route('/download_booking/<int:booking_id>')
def download_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('account'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, u.name, u.email, u.nin, u.id AS user_id
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.id = %s AND u.id = %s
    """, (booking_id, session['user_id']))
    booking = cursor.fetchone()
    cursor.close()
    conn.close()

    if not booking:
        return "Booking not found."

    # Use your booking_slip.html and pass 'booking'
    pdf_html = render_template('booking_slip.html', booking=booking)

    pdf_stream = BytesIO()
    pisa_status = pisa.CreatePDF(pdf_html, dest=pdf_stream)
    if pisa_status.err:
        return "PDF generation failed."

    pdf_stream.seek(0)
    response = make_response(pdf_stream.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=booking_{booking_id}.pdf'
    return response

# Social login callbacks
@app.route("/google_callback")
def google_callback():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if resp.ok:
        user_info = resp.json()
        return handle_social_login(user_info)
    return "Google login failed"

@app.route("/facebook_callback")
def facebook_callback():
    if not facebook.authorized:
        return redirect(url_for("facebook.login"))
    resp = facebook.get("/me?fields=id,name,email")
    if resp.ok:
        return handle_social_login(resp.json())
    return "Facebook login failed"

@app.route("/linkedin_callback")
def linkedin_callback():
    if not linkedin.authorized:
        return redirect(url_for("linkedin.login"))
    email_resp = linkedin.get("emailAddress?q=members&projection=(elements*(handle~))")
    profile_resp = linkedin.get("me")
    if email_resp.ok and profile_resp.ok:
        email = email_resp.json()["elements"][0]["handle~"]["emailAddress"]
        name = profile_resp.json().get("localizedFirstName", "LinkedInUser")
        return handle_social_login({"email": email, "name": name})
    return "LinkedIn login failed"

def handle_social_login(user_info):
    email = user_info['email']
    name = user_info.get('name', 'User').upper()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (name, email, password, nin) VALUES (%s, %s, %s, %s)", 
                       (name, email, "", ""))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

    session['user_id'] = user['id']
    cursor.close()
    conn.close()

    return redirect(url_for('dashboard'))



# ... [rest of your code above remains unchanged]

# This version was previously duplicated and is now removed
# def generate_reset_token(user, expires_sec=3600):
#     s = Serializer(current_app.config['SECRET_KEY'])
#     return s.dumps({'user_id': user['id']})

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = Serializer(os.getenv('SECRET_KEY'))
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            flash('Invalid user.', 'danger')
            return redirect(url_for('forgot_password'))

        if request.method == 'POST':
            new_password = request.form['password']
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed, email))
            conn.commit()
            flash('Your password has been reset!', 'success')
            return redirect(url_for('account'))

    except (BadSignature, SignatureExpired):
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))

    return render_template('reset_password.html', token=token)



def generate_reset_token(user):
    serializer = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))
    return serializer.dumps(user['email'], salt='password-reset-salt')




@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = get_user_by_email(email)
        if user:
            token = generate_reset_token(user)
            reset_url = url_for('reset_password', token=token, _external=True)
            send_reset_email(user['email'], reset_url)
        flash('If your email is registered, a reset link has been sent.', 'info')
        return redirect(url_for('account'))
    return render_template('forgot_password.html')










def send_reset_email(recipient_email, reset_url):
    msg = EmailMessage()
    msg['Subject'] = 'Password Reset Request'
    msg['From'] = os.getenv('EMAIL_SENDER')  # e.g. 'noreply@yourapp.com'
    msg['To'] = recipient_email
    msg.set_content(f"""
Hi,

You requested a password reset. Click the link below to reset your password:

{reset_url}

If you did not request this, please ignore this email.

Thanks,
Your App Team
""")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.getenv('EMAIL_SENDER'), os.getenv('EMAIL_PASSWORD'))
            smtp.send_message(msg)
    except Exception as e:
        print("Error sending email:", e)



@app.route('/booking_confirmation/<int:booking_id>')
def booking_confirmation(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('account'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.*, u.name AS full_name
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.id = %s AND b.user_id = %s
    """, (booking_id, session['user_id']))
    
    booking = cursor.fetchone()

    cursor.close()
    conn.close()

    if not booking:
        return "Booking not found."

    # Generate QR code
    qr_data = f"http://localhost:5000/payment/{booking_id}"
    img = qrcode.make(qr_data)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render_template("booking_confirmation.html", booking=booking, qr_code=qr_code_base64)



@app.route('/payment_success/<int:booking_id>')
def payment_success_page(booking_id):
    return render_template('payment_success.html', booking_id=booking_id)


@app.route('/process_payment', methods=['POST'])
def process_payment():
    booking_id = request.form.get('booking_id')

    if not booking_id or not booking_id.isdigit():
        return "Invalid booking ID", 400

    booking_id = int(booking_id)

    # Process the payment...
    return redirect(url_for('payment_success_page', booking_id=booking_id))

@app.route('/test_payment_success/<int:booking_id>')
def test_payment_success(booking_id):
    # Simulate a successful payment scenario
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('account'))

    # Fetch booking details
    booking = db.get_booking(booking_id, user_id)
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('dashboard'))

    # For testing purposes, manually mark the booking as paid
    db.mark_booking_paid(booking_id)  # This would mark the booking as "paid" in your database

    # Flash a success message
    flash('Payment was successful for booking ID: {}'.format(booking_id), 'success')

    # Redirect to the payment success page
    return redirect(url_for('payment_success', booking_id=booking_id))


@app.route('/payment/<int:booking_id>')
def payment_page(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('account'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bookings WHERE id = %s AND user_id = %s", (booking_id, session['user_id']))
    booking = cursor.fetchone()
    cursor.close()
    conn.close()

    if not booking:
        return "Booking not found."

    return render_template('payment_page.html', booking=booking)



@app.route('/confirm_payment/<int:booking_id>', methods=['POST'])
def confirm_payment(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('account'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET payment_status = 'Paid' WHERE id = %s AND user_id = %s", (booking_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('dashboard'))

@app.route('/download_payment_receipt/<int:booking_id>')
def download_payment_receipt(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('account'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, u.name, u.email, u.nin
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.id = %s AND u.id = %s
    """, (booking_id, session['user_id']))
    booking = cursor.fetchone()
    cursor.close()
    conn.close()

    if not booking:
        return "Booking not found."

    if booking['payment_status'] != 'Paid':
        return "Payment not confirmed yet."

    # Generate QR code (for demonstration)
    qr = qrcode.make(f"Booking ID: JEF-{booking['id']}\nName: {booking['name']}")
    qr_stream = BytesIO()
    qr.save(qr_stream, format='PNG')
    qr_base64 = base64.b64encode(qr_stream.getvalue()).decode('utf-8')

    # Render PDF using a dedicated receipt template
    receipt_html = render_template('payment_receipt.html', booking=booking, qr_base64=qr_base64)

    pdf_stream = BytesIO()
    pisa_status = pisa.CreatePDF(receipt_html, dest=pdf_stream)
    if pisa_status.err:
        return "Receipt PDF generation failed."

    pdf_stream.seek(0)
    response = make_response(pdf_stream.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=receipt_JEF-{booking_id}.pdf'
    return response





def generate_qr_code_for_payment(booking):
    payment_url = f"https://payment-url.com/{booking['id']}/paid"
    qr_code = qrcode.make(payment_url)
    qr_code_path = f"./static/qrcodes/payment_qr_{booking['id']}.png"
    qr_code.save(qr_code_path)
    return qr_code_path




def generate_payment_pdf(booking):
    pdf_path = f'./static/pdfs/payment_confirmation_{booking["id"]}.pdf'
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    c.drawString(100, 750, f"JEFJET FLIGHT BOOKINGS")
    c.drawString(100, 730, f"Petroleum Training Institute Warri, Delta-Nigeria")
    c.drawString(100, 710, f"Booking ID: {booking['id']}")
    c.drawString(100, 690, f"Trip Type: {booking['trip_type']}")
    c.drawString(100, 670, f"From: {booking['from_location']}")
    c.drawString(100, 650, f"To: {booking['to_location']}")
    c.drawString(100, 630, f"Depart: {booking['depart_date']}")
    c.drawString(100, 610, f"Return: {booking['return_date']}")
    c.drawString(100, 590, f"Adults: {booking['adults']}")
    c.drawString(100, 570, f"Children: {booking['children']}")
    c.drawString(100, 550, f"Class: {booking['class_of_travel']}")
    c.drawString(100, 530, f"Airline: {booking['airline_name']}")
    c.drawString(100, 510, f"Payment Status: Paid")

    c.save()
    return pdf_path



from email_utils import send_email  # adjust to match your actual import

from flask import flash, redirect, url_for
from email_utils import send_email_notification

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('account'))  # Ensure user is logged in

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if the booking exists and belongs to the user
        cursor.execute("SELECT * FROM bookings WHERE id = %s AND user_id = %s", (booking_id, user_id))
        booking = cursor.fetchone()

        if not booking:
            flash('Booking not found or you are not authorized to cancel it.', 'danger')
            return redirect(url_for('dashboard'))

        # Check if the user has already canceled two bookings
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE user_id = %s AND status = 'cancelled'", (user_id,))
        cancel_count = cursor.fetchone()[0]

        if cancel_count >= 2:
            flash('You have reached the limit of cancellations allowed.', 'danger')
            return redirect(url_for('dashboard'))

        # Update the booking status to 'cancelled'
        cursor.execute("UPDATE bookings SET status = 'cancelled' WHERE id = %s", (booking_id,))
        conn.commit()

        # Send email notification
        send_email_notification(user_id, booking_id, "cancellation")

        flash('Your booking has been successfully cancelled.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f"An error occurred while cancelling the booking: {e}", 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('dashboard'))




@app.route('/qr/<int:booking_id>')
def generate_qr(booking_id):
    payment_url = url_for('payment', booking_id=booking_id, _external=True)
    img = qrcode.make(payment_url)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')







if __name__ == '__main__':
    app.run(debug=True, port=5001)
