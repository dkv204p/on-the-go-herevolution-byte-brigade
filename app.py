from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_mysqldb import MySQL
import bcrypt
import secrets
from twilio.rest import Client


app = Flask(__name__, static_url_path='/static')
app.secret_key = "test_secret_key"

app.config['TWILIO_ACCOUNT_SID'] = 'ACdab12cfc9328b73a14594443f9a08d08'
app.config['TWILIO_AUTH_TOKEN'] = 'e227dfc0cf59e9c886d5352d4da1a784'

twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'otg'

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/maps')
def maps():
    return render_template('maps.html')

@app.route('/sign-in')
def signInPage():
    return render_template('signin-signup.html')

# admin dashboards
@app.route('/fire-admin-dashboard')
def fireEmergencyDashboard():
    return render_template('fire-emergency-dashboard/index.html')

@app.route('/hospital-admin-dashboard')
def hospitalEmergencyDashboard():
    return render_template('hospital-admin-dashboard/index.html')

@app.route('/police-admin-dashboard')
def policeDashboard():
    return render_template('police-admin-dashboard/index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        
        # Check if the email already exists in the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()
        cur.close()
        
        if existing_user:
            return "Email already registered. Please use a different email address. <a href=\"/register\">Go back</a>"
        # If the email is not already registered, proceed with registration
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (fullname, email, password) VALUES (%s, %s, %s)", (name, email, password))
        mysql.connection.commit()
        cur.close()
        return "Registered Successfully! You can continue to <a href=\"/sign-in\">login now</a>"
    else:
        # Handle GET request, e.g., display registration form
        # You can return HTML code for the registration form here
        return "This is the registration form. You can fill it out here."

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_row = cur.fetchone()
        cur.close()
        if user_row:
            user = {
                'id': user_row[0],
                'name': user_row[1],
                'email': user_row[2],
                'password': user_row[3]
            }
            if bcrypt.checkpw(password, user['password'].encode('utf-8')):
                session['loggedin'] = True
                session['id'] = user['id']
                session['name'] = user['name']
                session['email'] = user['email']
                return "Logged In you can continue to <a href=\"/\">Home</a>"
        
        return 'Invalid email/password combination'

@app.route('/my-profile')
def myProfile():
    return render_template('my-profile.html')

@app.route('/update-location', methods=['POST'])
def update_location():
    if request.method == 'POST':
        email = session.get('email')  # Retrieve email from session
        if not email:
            return 'Email not found in session', 400  # Return an error response if email is not found in session

        try:
            lat = request.form['lat']  # Retrieve latitude from form data
            lon = request.form['lon']  # Retrieve longitude from form data

            # Check if lat and lon are present in the form data
            if not lat or not lon:
                return 'Latitude or Longitude not provided', 400

            with mysql.connection.cursor() as cursor:
                cursor.execute("INSERT INTO near (email, lat, lon) VALUES (%s, %s, %s)", (email, lat, lon))
                if cursor.rowcount == 0:  # If no rows were affected, insert a new record
                    cursor.execute("UPDATE near SET lat = %s, lon = %s WHERE email = %s", (lat, lon, email))

            mysql.connection.commit()  # Commit the transaction
            return 'Location updated successfully'
        except KeyError as e:
            return f'Missing key in form data: {e}', 400  # Return error response with status code 400
        except Exception as e:
            mysql.connection.rollback()  # Rollback the transaction in case of an error
            return f'Error updating location: {e}', 500  # Return error response with status code 500

@app.route('/insert_data', methods=['POST'])
def insert_data():
    # Extract latitude and longitude from received form data
    lat = request.form['lat']
    lon = request.form['lon']

    try:
        # Insert data into the database
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO emergency (email, lat, lon) VALUES (%s, %s, %s)", (session['email'], lat, lon))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Data inserted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send_sms', methods=['POST'])
def send_sms():
    lat = request.form['lat']
    lon = request.form['lon']
    recipient = '+919119215296'
    message_body = "I am in an emergency situation, Please help me, I am at LATITUDE: " + lat + " LONGITUDE: " + lon

    twilio_client.messages.create(
        body=message_body,
        from_='+19382010316',
        to=recipient
    )

@app.route('/insert_data_medical', methods=['POST'])
def insert_data_medical():
    email = session['email']
    lat = request.form['lat']
    lon = request.form['lon']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO medical (email, lat, lon) VALUES (%s, %s, %s)", (email, lat, lon))
    mysql.connection.commit()
    cur.close()

@app.route('/insert_data_fire', methods=['POST'])
def insert_data_fire():
    email = session['email']
    lat = request.form['lat']
    lon = request.form['lon']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO fire (email, lat, lon) VALUES (%s, %s, %s)", (email, lat, lon))
    mysql.connection.commit()
    cur.close()

@app.route('/insert_data_police', methods=['POST'])
def insert_data_police():
    email = session['email']
    lat = request.form['lat']
    lon = request.form['lon']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO police (email, lat, lon) VALUES (%s, %s, %s)", (email, lat, lon))
    mysql.connection.commit()
    cur.close()



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)