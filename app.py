from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import redis
import pymongo
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

app = Flask(__name__)
app.config['SECRET_KEY'] = 'meowmeowmeowmeowmeow'  # more secure if needed
app.config['SESSION_COOKIE_SECURE'] = False # not secure so not True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
socketio = SocketIO(app, async_mode='gevent')

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Redis and MongoDB connections
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
mongo_client = pymongo.MongoClient('mongodb://localhost:27017/')
db = mongo_client['trainBooking']
bookings_collection = db['bookings']
users_collection = db['users']


# User model for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, username, email):
        self.id = user_id
        self.username = username
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    try:
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if user:
            return User(str(user['_id']), user['username'], user['email'])
        print(f"User {user_id} not found")
        return None
    except Exception as e:
        print(f"Error loading user {user_id}: {e}")
        return None


# init seats (6 coaches, 20 seats each)
SEATS = {}
for coach in range(1, 7):
    for seat in range(1, 21):
        seat_id = f'C{coach}-S{seat}'
        SEATS[seat_id] = {'status': 'available', 'user': None}


@app.route('/')
@login_required
def index():
    print(f"Index accessed by user: {current_user.username}")
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print(f"User {current_user.username} already authenticated, redirecting to index")
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"Login attempt for email: {email}")
        try:
            user = users_collection.find_one({'email': email})
            if user and check_password_hash(user['password'], password):
                user_obj = User(str(user['_id']), user['username'], user['email'])
                login_user(user_obj)
                session.permanent = True
                print(f"Login successful for {user['username']}")
                return redirect(url_for('index'))
            else:
                print("Invalid credentials")
                flash('Invalid email or password', 'error')
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred. Please try again.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"Register attempt for {email}")
        try:
            if users_collection.find_one({'email': email}):
                print("Email already registered")
                flash('Email already registered', 'error')
            else:
                user_id = users_collection.insert_one({
                    'username': username,
                    'email': email,
                    'password': generate_password_hash(password)
                }).inserted_id
                print(f"User {username} registered with ID {user_id}")
                login_user(User(str(user_id), username, email))
                return redirect(url_for('index'))
        except Exception as e:
            print(f"Register error: {e}")
            flash('An error occurred. Please try again.', 'error')
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    print(f"User {current_user.username} logging out")
    logout_user()
    return redirect(url_for('login'))


@app.route('/receipt/<booking_id>')
@login_required
def receipt(booking_id):
    try:
        booking = bookings_collection.find_one({'_id': ObjectId(booking_id), 'userId': current_user.id})
        if booking:
            print(f"Receipt accessed for booking {booking_id} by user {current_user.username}")
            return render_template('receipt.html', booking=booking)
        else:
            print(f"Booking {booking_id} not found or unauthorized for user {current_user.username}")
            flash('Booking not found or unauthorized', 'error')
            return render_template('receipt.html', booking=None)
    except Exception as e:
        print(f"Error accessing receipt {booking_id}: {e}")
        flash('An error occurred while accessing the receipt', 'error')
        return render_template('receipt.html', booking=None)


@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        print(f"Socket.IO connected for user: {current_user.username}")


@socketio.on('lockSeat')
def lock_seat(data):
    if not current_user.is_authenticated:
        print("Unauthenticated Socket.IO attempt")
        return
    seat_id = data['seatId']
    client_id = data['clientId']
    lock_key = f'lock:{seat_id}'

    if SEATS[seat_id]['status'] == 'available':
        locked = redis_client.set(lock_key, client_id, ex=300, nx=True)
        if locked:
            SEATS[seat_id]['status'] = 'locked'
            SEATS[seat_id]['user'] = client_id
            emit('seatUpdate', {'seatId': seat_id, 'status': 'locked'}, broadcast=True)


@socketio.on('unlockSeat')
def unlock_seat(data):
    if not current_user.is_authenticated:
        print("Unauthenticated Socket.IO attempt")
        return
    seat_id = data['seatId']
    lock_key = f'lock:{seat_id}'
    redis_client.delete(lock_key)
    SEATS[seat_id]['status'] = 'available'
    SEATS[seat_id]['user'] = None
    emit('seatUpdate', {'seatId': seat_id, 'status': 'available'}, broadcast=True)


@socketio.on('confirmBooking')
def confirm_booking(data):
    if not current_user.is_authenticated:
        print("Unauthenticated Socket.IO attempt")
        return
    seat_id = data['seatId']
    client_id = data['clientId']
    lock_key = f'lock:{seat_id}'

    if redis_client.get(lock_key) == client_id:
        booking = {
            'seatId': seat_id,
            'trainNumber': 'T123',
            'departure': '10:00 AM',
            'arrival': '6:00 PM',
            'amount': 50,
            'bookedAt': datetime.datetime.now(),
            'userId': current_user.id
        }
        result = bookings_collection.insert_one(booking)
        redis_client.delete(lock_key)
        SEATS[seat_id]['status'] = 'booked'
        SEATS[seat_id]['user'] = None
        emit('seatUpdate', {'seatId': seat_id, 'status': 'booked', 'bookingId': str(result.inserted_id)},
             broadcast=True)


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)