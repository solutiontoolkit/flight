import mysql.connector
import pymysql
import os
import mysql.connector
from dotenv import load_dotenv

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        ssl_ca=rf"C:\Users\Joshua.STK-PROJECT\Desktop\flight\ca.pem"
    )




load_dotenv()

def get_db_connection():
    connection = mysql.connector.connect(
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    database=os.environ["DB_NAME"],
    ssl_ca=os.environ.get("ssl_ca")  # optional if not using SSL
)



def get_booking(booking_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM bookings WHERE id = %s AND user_id = %s",
        (booking_id, user_id)
    )
    booking = cursor.fetchone()
    cursor.close()
    conn.close()
    return booking

def get_bookings(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM bookings 
        WHERE user_id = %s AND status != 'cancelled' 
        ORDER BY created_at DESC
    """, (user_id,))
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()

    for booking in bookings:
        if 'payment_status' in booking and booking['payment_status']:
            booking['payment_status'] = booking['payment_status'].lower()

    return bookings







def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = "SELECT * FROM users WHERE email = %s"
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


# database/db.py

def get_booking_by_id(booking_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, u.name, u.email, u.nin
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.id = %s AND b.user_id = %s
    """, (booking_id, user_id))
    booking = cursor.fetchone()
    cursor.close()
    conn.close()

    if booking:
        if 'payment_status' in booking and booking['payment_status']:
            booking['payment_status'] = booking['payment_status'].lower()
        if 'status' in booking and booking['status']:
            booking['status'] = booking['status'].lower()

    return booking


def mark_booking_paid(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # ✅ Always update to lowercase 'paid'
    cursor.execute("UPDATE bookings SET payment_status = 'paid' WHERE id = %s", (booking_id,))
    cursor.execute("UPDATE bookings SET status = 'PAID' WHERE id = %s", (booking_id,))

    conn.commit()
    cursor.close()
    conn.close()

