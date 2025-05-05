


from flask import Flask, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session

# Your existing routes...

@app.route('/dashboard')
def dashboard():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('account'))  # Redirect to login
    return render_template('dashboard.html')  # Your user dashboard

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'user_id' not in session:
        return redirect(url_for('account'))  # Force login before booking
    return render_template('bookin.html')


@app.route('/')
def home():
    return render_template('index.html')



@app.route('/account')
def account():
    return render_template('login.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
