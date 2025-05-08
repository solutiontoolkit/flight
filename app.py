from flask import Flask, render_template, redirect, url_for, session, request, flash
from database.db import get_connection
import bcrypt

import os
from dotenv import load_dotenv

from flask import make_response
from xhtml2pdf import pisa
from io import BytesIO
from flask import render_template_string
from email_utils import send_welcome_email


# Import blueprints and handlers from the new social_auth module
from social_auth import (
    google_bp, facebook_bp, linkedin_bp,
    handle_social_login
)
from flask_dance.contrib.google import google
from flask_dance.contrib.facebook import facebook
from flask_dance.contrib.linkedin import linkedin

app = Flask(__name__)


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
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # ✅ First fetch user info
        cursor.execute("SELECT id, name, email, nin FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()  # Must fetch before new execute

        # ✅ Then fetch bookings
        cursor.execute("SELECT * FROM bookings WHERE user_id = %s", (user_id,))
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

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

  

from flask import flash

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name'].upper()
    email = request.form['email']
    password = request.form['password']
    nin = request.form['NIN']
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, email, password, nin) VALUES (%s, %s, %s, %s)",
                       (name, email, hashed, nin))
        conn.commit()

        # ✅ Send welcome email (surrounded with try to prevent crash)
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
        return redirect(url_for('show_signin'))  # or back to /signup if you have a signup page
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('show_signin'))  # or to 'dashboard'






@app.route('/signin', methods=['POST'])
def signin():
    identifier = request.form['identifier']
    password = request.form['password']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s OR nin = %s", (identifier, identifier))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        session['user_id'] = user['id']
        flash('You have successfully logged in!', 'success')  # Flash message on successful login
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid email/NIN or password. Please try again.', 'danger')  # Flash message on failed login
        return render_template('login.html')



@app.route('/signin', methods=['GET'])
def show_signin():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('account'))

# --- Social Login Callbacks ---

@app.route("/google_callback")
def google_callback():
    if not google.authorized:
        return redirect(url_for("google.login"))

    # Fetch user info from Google
    resp = google.get("/oauth2/v2/userinfo")
    
    if resp.ok:
        user_info = resp.json()
       
        print("Google login successful, user info:", user_info)

        # Handle social login and redirect
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
    
    # Check if the user exists in the database
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        # Create a new user if not found
        cursor.execute(
            "INSERT INTO users (name, email, password, nin) VALUES (%s, %s, %s, %s)",
            (name, email, "", "")  # Empty password and NIN
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

    # Set the user_id in the session
    session['user_id'] = user['id']
    
    cursor.close()
    conn.close()
    
    # Redirect to the dashboard after login
    return redirect(url_for('dashboard'))





#####------- booking route for submission

@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    if 'user_id' not in session:
        return redirect(url_for('account'))

    data = request.form
    conn = get_connection()
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
            data.get('trip-type'),
            data.get('from'),
            data.get('to'),
            data.get('depart'),
            data.get('return'),
            data.get('adults'),
            data.get('children'),
            data.get('infants'),
            data.get('class-of-travel'),
            data.get('airline-name')
        ))
        conn.commit()
    except Exception as e:
        print("Booking error:", e)
        return "Booking submission failed: " + str(e)
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('dashboard'))



####-------route for downloading bookings

from flask import make_response, render_template_string, session, redirect, url_for
from io import BytesIO
from xhtml2pdf import pisa
from database.db import get_connection  # Replace with actual import

@app.route('/download_booking/<int:booking_id>')
def download_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('account'))

    conn = get_connection()
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

    pdf_html = render_template_string("""
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; font-size: 14px; }
            .header { text-align: center; margin-bottom: 20px; }
            .header img { max-width: 90px; }
            h2 { text-align: center; }
            .info, .booking-details { margin-bottom: 15px; }
            .info p, .booking-details p { margin: 5px 0; }
            hr { margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <img src="{{ url_for('static', filename='img/jet_logo.jpg') }}">
            <div><strong>JEFJET FLIGHT BOOKINGS</strong></div>
            <div style="font-size: 13px;">Petroleum Training Institute Warri, Delta-Nigeria</div>
        </div>

        <h2>Flight Booking Slip</h2>

        <div class="info">
            <p><strong>Name:</strong> {{ booking.name.upper() }}</p>
            <p><strong>User ID:</strong> {{ booking.user_id }}</p>
            <p><strong>Email:</strong> {{ booking.email }}</p>
            <p><strong>NIN:</strong> {{ booking.nin }}</p>
        </div>

        <hr>

        <div class="booking-details">
            <p><strong>Trip Type:</strong> {{ booking.trip_type }}</p>
            <p><strong>From:</strong> {{ booking.from_location }}</p>
            <p><strong>To:</strong> {{ booking.to_location }}</p>
            <p><strong>Departure Date:</strong> {{ booking.depart_date }}</p>
            <p><strong>Return Date:</strong> {{ booking.return_date }}</p>
            <p><strong>Passengers:</strong> {{ booking.adults }} adults, {{ booking.children }} children, {{ booking.infants }} infants</p>
            <p><strong>Class:</strong> {{ booking.class_of_travel }}</p>
            <p><strong>Preferred Airline:</strong> {{ booking.airline_name }}</p>
            <p><strong>Booking Date:</strong> {{ booking.created_at }}</p>
        </div>
    </body>
    </html>
    """, booking=booking)

    pdf_stream = BytesIO()
    pisa_status = pisa.CreatePDF(pdf_html, dest=pdf_stream)
    if pisa_status.err:
        return "PDF generation failed."

    pdf_stream.seek(0)
    response = make_response(pdf_stream.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=booking_{booking_id}.pdf'
    return response


load_dotenv()  

app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')




if __name__ == '__main__':
    app.run(debug=True, port=5001)
