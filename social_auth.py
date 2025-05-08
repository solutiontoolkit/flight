# social_auth.py

from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from flask_dance.contrib.linkedin import make_linkedin_blueprint, linkedin
from flask import session, redirect, url_for
from database.db import get_connection





google_bp = make_google_blueprint(
    client_id="388654387598-v3g8ro450e6ngmh4fj9rluh7pfvlbbe9.apps.googleusercontent.com",
    client_secret="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",
    scope=["profile", "email"],
    redirect_to="google_callback"
)

facebook_bp = make_facebook_blueprint(
    client_id="YOUR_FACEBOOK_CLIENT_ID",
    client_secret="YOUR_FACEBOOK_CLIENT_SECRET",
    scope=["email"],
    redirect_to="facebook_callback"
)

linkedin_bp = make_linkedin_blueprint(
    client_id="YOUR_LINKEDIN_CLIENT_ID",
    client_secret="YOUR_LINKEDIN_CLIENT_SECRET",
    scope=["r_liteprofile", "r_emailaddress"],
    redirect_to="linkedin_callback"
)

# --- Handlers ---

def handle_social_login(user_info):
    email = user_info.get("email")
    name = user_info.get("name", email.split('@')[0])

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (name, email, password, nin) VALUES (%s, %s, %s, %s)",
            (name, email, "", "")
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

    session['user_id'] = user['id']
    cursor.close()
    conn.close()
