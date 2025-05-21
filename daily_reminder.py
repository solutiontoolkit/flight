from datetime import date, timedelta
from app import app  # Import your Flask app instance here
from database.db import get_upcoming_flights, get_user_by_id
from email_utils import send_flight_reminder_email

def send_daily_reminders():
    tomorrow = date.today() + timedelta(days=1)

    # Send reminders for DEPARTURE flights tomorrow
    departure_bookings = get_upcoming_flights(flight_date=tomorrow, flight_type="departure")
    for booking in departure_bookings:
        user = get_user_by_id(booking['user_id'])
        if user:
            send_flight_reminder_email(user, booking, flight_type="departure")

    # Send reminders for RETURN flights tomorrow (only if return_date != depart_date)
    return_bookings = get_upcoming_flights(flight_date=tomorrow, flight_type="return")
    for booking in return_bookings:
        if booking['return_date'] != booking['depart_date']:
            user = get_user_by_id(booking['user_id'])
            if user:
                send_flight_reminder_email(user, booking, flight_type="return")

if __name__ == "__main__":
    with app.app_context():
        send_daily_reminders()
