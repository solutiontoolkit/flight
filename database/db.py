import mysql.connector
import pymysql
import os
import mysql.connector
from dotenv import load_dotenv


load_dotenv()  # Make sure this is correct

def get_connection():
    try:
        conn = mysql.connector.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        ssl_ca=os.environ.get("ssl_ca")  # optional if not using SSL
)
        return conn
    except mysql.connector.Error as err:
        print("❌ Database connection failed:", err)
        return None




import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT', 3306)),
            ssl_ca=os.getenv('ssl_ca')  # if used
        )
        if conn.is_connected():
            return conn
        else:
            print("❌ Database connection failed: Not connected")
            return None
    except Error as e:
        print(f"❌ Database connection error: {e}")
        return None





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

''''
def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        return user
    except Exception as e:
        print("Error getting user by ID:", e)
        return None
    finally:
        cursor.close()
        conn.close()'''


def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user



def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = "SELECT * FROM users WHERE email = %s"
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


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
    cursor.execute("UPDATE bookings SET payment_status = 'paid' WHERE id = %s", (booking_id,))
    cursor.execute("UPDATE bookings SET status = 'PAID' WHERE id = %s", (booking_id,))

    conn.commit()
    cursor.close()
    conn.close()

def get_upcoming_flights(flight_date, flight_type="departure"):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if flight_type == "departure":
        query = """
            SELECT * FROM bookings
            WHERE depart_date = %s AND payment_status = 'paid'
        """
    else:  # return flight
        query = """
            SELECT * FROM bookings
            WHERE return_date = %s AND payment_status = 'paid'
        """

    cursor.execute(query, (flight_date,))
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return bookings


