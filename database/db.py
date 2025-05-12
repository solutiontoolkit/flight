import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mathematics",
        database="jet_project"
    )


import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )



def get_booking(booking_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # Use dictionary=True to fetch data as dict
    query = """
        SELECT * FROM bookings 
        WHERE id = %s AND user_id = %s
    """
    cursor.execute(query, (booking_id, user_id))
    booking = cursor.fetchone()  # fetchone will return None if no result
    cursor.close()
    conn.close()
    return booking

import pymysql
from database.db import get_db_connection  # adjust based on your project structure

def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = "SELECT * FROM users WHERE email = %s"
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user
