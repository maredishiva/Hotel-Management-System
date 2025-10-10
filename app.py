from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, date
import sqlite3
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_name: str = "hotel_management.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Create rooms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                room_number INTEGER PRIMARY KEY,
                room_type TEXT NOT NULL,
                price REAL NOT NULL,
                capacity INTEGER NOT NULL,
                is_occupied BOOLEAN DEFAULT 0,
                clean BOOLEAN DEFAULT 1,
                description TEXT
            )
        ''')
        
        # Create guests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guests (
                guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                address TEXT,
                id_type TEXT,
                id_number TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create reservations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservations (
                reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guest_id INTEGER,
                room_number INTEGER,
                check_in DATE NOT NULL,
                check_out DATE NOT NULL,
                total_amount REAL NOT NULL,
                is_checked_in BOOLEAN DEFAULT 0,
                is_checked_out BOOLEAN DEFAULT 0,
                status TEXT DEFAULT 'confirmed',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (guest_id) REFERENCES guests (guest_id),
                FOREIGN KEY (room_number) REFERENCES rooms (room_number)
            )
        ''')
        
        # Create payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_id INTEGER,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'completed',
                FOREIGN KEY (reservation_id) REFERENCES reservations (reservation_id)
            )
        ''')
        
        # Insert sample data if empty
        cursor.execute("SELECT COUNT(*) FROM rooms")
        if cursor.fetchone()[0] == 0:
            sample_rooms = [
                (101, "Standard Single", 99.99, 1, 0, 1, "Cozy room with single bed"),
                (102, "Standard Double", 149.99, 2, 0, 1, "Comfortable room with double bed"),
                (103, "Deluxe Suite", 299.99, 4, 0, 1, "Spacious suite with living area"),
                (201, "Standard Single", 99.99, 1, 0, 1, "Cozy room with single bed"),
                (202, "Standard Double", 149.99, 2, 0, 1, "Comfortable room with double bed"),
                (203, "Executive Suite", 399.99, 3, 0, 1, "Luxurious suite with premium amenities")
            ]
            cursor.executemany(
                "INSERT INTO rooms (room_number, room_type, price, capacity, is_occupied, clean, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                sample_rooms
            )
        
        conn.commit()
        conn.close()

    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL query and return cursor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return cursor

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        """Fetch all results from query"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Fetch single result from query"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

app = Flask(__name__)
app.secret_key = 'hotel_management_secret_key_2024'
db = Database()

@app.route('/')
def index():
    """Dashboard page"""
    try:
        # Get hotel statistics
        stats = {
            'total_rooms': db.fetch_one("SELECT COUNT(*) as count FROM rooms")['count'],
            'occupied_rooms': db.fetch_one("SELECT COUNT(*) as count FROM rooms WHERE is_occupied = 1")['count'],
            'total_guests': db.fetch_one("SELECT COUNT(*) as count FROM guests")['count'],
            'active_reservations': db.fetch_one("SELECT COUNT(*) as count FROM reservations WHERE is_checked_out = 0")['count'],
            'available_rooms': db.fetch_one("SELECT COUNT(*) as count FROM rooms WHERE is_occupied = 0 AND clean = 1")['count']
        }
        
        # Calculate occupancy rate
        if stats['total_rooms'] > 0:
            stats['occupancy_rate'] = round((stats['occupied_rooms'] / stats['total_rooms']) * 100, 1)
        else:
            stats['occupancy_rate'] = 0
        
        # Get total revenue
        revenue_data = db.fetch_one("SELECT SUM(amount) as total FROM payments")
        stats['total_revenue'] = revenue_data['total'] or 0.0
        
        # Get recent reservations
        recent_reservations = db.fetch_all('''
            SELECT r.*, g.name as guest_name, g.phone, rm.room_type 
            FROM reservations r 
            JOIN guests g ON r.guest_id = g.guest_id 
            JOIN rooms rm ON r.room_number = rm.room_number 
            ORDER BY r.created_date DESC LIMIT 5
        ''')
        
        return render_template('index.html', stats=stats, recent_reservations=recent_reservations)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('index.html', stats={}, recent_reservations=[])

@app.route('/rooms')
def rooms():
    """Display all rooms"""
    try:
        rooms_data = db.fetch_all('''
            SELECT * FROM rooms ORDER BY room_number
        ''')
        return render_template('rooms.html', rooms=rooms_data)
    except Exception as e:
        flash(f'Error loading rooms: {str(e)}', 'error')
        return render_template('rooms.html', rooms=[])

@app.route('/guests')
def guests():
    """Display all guests"""
    try:
        guests_data = db.fetch_all('''
            SELECT * FROM guests ORDER BY created_date DESC
        ''')
        return render_template('guests.html', guests=guests_data)
    except Exception as e:
        flash(f'Error loading guests: {str(e)}', 'error')
        return render_template('guests.html', guests=[])

@app.route('/reservations')
def reservations():
    """Display all reservations"""
    try:
        reservations_data = db.fetch_all('''
            SELECT 
                r.reservation_id,
                r.guest_id,
                r.room_number,
                r.check_in,
                r.check_out,
                r.total_amount,
                r.is_checked_in,
                r.is_checked_out,
                r.status,
                r.created_date,
                g.name as guest_name,
                g.email,
                g.phone,
                g.address,
                rm.room_type,
                rm.price
            FROM reservations r 
            JOIN guests g ON r.guest_id = g.guest_id 
            JOIN rooms rm ON r.room_number = rm.room_number 
            ORDER BY r.created_date DESC
        ''')
        
        print(f"DEBUG: Found {len(reservations_data)} reservations")
        
        return render_template('reservations.html', reservations=reservations_data)
    except Exception as e:
        flash(f'Error loading reservations: {str(e)}', 'error')
        print(f"ERROR: {str(e)}")
        return render_template('reservations.html', reservations=[])

@app.route('/make_reservation', methods=['GET', 'POST'])
def make_reservation():
    """Make a new reservation"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            room_number = int(request.form['room_number'])
            check_in_str = request.form['check_in']
            check_out_str = request.form['check_out']
            address = request.form.get('address', '')
            id_type = request.form.get('id_type', '')
            id_number = request.form.get('id_number', '')
            
            # Convert string dates to date objects - FIXED DATETIME ERROR
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            
            # Validate dates
            if check_in >= check_out:
                flash('Check-out date must be after check-in date!', 'error')
                return redirect(url_for('make_reservation'))
            
            if check_in < date.today():
                flash('Check-in date cannot be in the past!', 'error')
                return redirect(url_for('make_reservation'))
            
            # Check room availability
            room = db.fetch_one('SELECT * FROM rooms WHERE room_number = ? AND is_occupied = 0 AND clean = 1', (room_number,))
            if not room:
                flash('Room is not available!', 'error')
                return redirect(url_for('make_reservation'))
            
            # Check for date conflicts
            conflicting_reservations = db.fetch_all('''
                SELECT * FROM reservations 
                WHERE room_number = ? 
                AND ((check_in <= ? AND check_out >= ?) OR (check_in <= ? AND check_out >= ?))
                AND is_checked_out = 0
            ''', (room_number, check_out.isoformat(), check_in.isoformat(), check_in.isoformat(), check_out.isoformat()))
            
            if conflicting_reservations:
                flash('Room is already booked for the selected dates!', 'error')
                return redirect(url_for('make_reservation'))
            
            # Get connection for transaction
            conn = db.get_connection()
            cursor = conn.cursor()
            
            try:
                # Register or find guest
                guest = db.fetch_one('SELECT * FROM guests WHERE email = ?', (email,))
                if not guest:
                    # Register new guest
                    cursor.execute(
                        'INSERT INTO guests (name, email, phone, address, id_type, id_number) VALUES (?, ?, ?, ?, ?, ?)',
                        (name, email, phone, address, id_type, id_number)
                    )
                    guest_id = cursor.lastrowid
                else:
                    guest_id = guest['guest_id']
                    # Update guest information if needed
                    cursor.execute(
                        'UPDATE guests SET name = ?, phone = ?, address = ?, id_type = ?, id_number = ? WHERE guest_id = ?',
                        (name, phone, address, id_type, id_number, guest_id)
                    )
                
                # Calculate total amount
                nights = (check_out - check_in).days
                total_amount = nights * room['price']
                
                # Create reservation
                cursor.execute(
                    '''INSERT INTO reservations 
                    (guest_id, room_number, check_in, check_out, total_amount) 
                    VALUES (?, ?, ?, ?, ?)''',
                    (guest_id, room_number, check_in.isoformat(), check_out.isoformat(), total_amount)
                )
                
                reservation_id = cursor.lastrowid
                conn.commit()
                
                flash(f'Reservation created successfully! Reservation ID: {reservation_id}', 'success')
                return redirect(url_for('reservations'))
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
            
        except Exception as e:
            flash(f'Error creating reservation: {str(e)}', 'error')
            return redirect(url_for('make_reservation'))
    
    # GET request - show available rooms
    try:
        available_rooms = db.fetch_all('SELECT * FROM rooms WHERE is_occupied = 0 AND clean = 1 ORDER BY room_number')
        return render_template('make_reservation.html', rooms=available_rooms)
    except Exception as e:
        flash(f'Error loading available rooms: {str(e)}', 'error')
        return render_template('make_reservation.html', rooms=[])

@app.route('/view_reservation/<int:reservation_id>')
def view_reservation(reservation_id):
    """View reservation details"""
    try:
        reservation = db.fetch_one('''
            SELECT 
                r.*,
                g.name as guest_name,
                g.email,
                g.phone,
                g.address,
                g.id_type,
                g.id_number,
                rm.room_type,
                rm.price,
                rm.capacity,
                rm.description
            FROM reservations r
            JOIN guests g ON r.guest_id = g.guest_id
            JOIN rooms rm ON r.room_number = rm.room_number
            WHERE r.reservation_id = ?
        ''', (reservation_id,))
        
        if not reservation:
            flash('Reservation not found!', 'error')
            return redirect(url_for('reservations'))
        
        # Calculate number of nights
        nights = 0
        if reservation['check_in'] and reservation['check_out']:
            try:
                if isinstance(reservation['check_in'], str):
                    check_in_date = datetime.strptime(reservation['check_in'], '%Y-%m-%d').date()
                else:
                    check_in_date = reservation['check_in']
                
                if isinstance(reservation['check_out'], str):
                    check_out_date = datetime.strptime(reservation['check_out'], '%Y-%m-%d').date()
                else:
                    check_out_date = reservation['check_out']
                
                nights = (check_out_date - check_in_date).days
            except Exception as e:
                print(f"Error calculating nights: {e}")
                nights = 0
        
        return render_template('view_reservation.html', reservation=reservation, nights=nights)
    except Exception as e:
        flash(f'Error loading reservation: {str(e)}', 'error')
        return redirect(url_for('reservations'))

@app.route('/edit_reservation/<int:reservation_id>', methods=['GET', 'POST'])
def edit_reservation(reservation_id):
    """Edit reservation"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            room_number = int(request.form['room_number'])
            check_in_str = request.form['check_in']
            check_out_str = request.form['check_out']
            address = request.form.get('address', '')
            
            # Convert string dates to date objects - FIXED DATETIME ERROR
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            
            # Validate dates
            if check_in >= check_out:
                flash('Check-out date must be after check-in date!', 'error')
                return redirect(url_for('edit_reservation', reservation_id=reservation_id))
            
            if check_in < date.today():
                flash('Check-in date cannot be in the past!', 'error')
                return redirect(url_for('edit_reservation', reservation_id=reservation_id))
            
            # Get current reservation
            current_reservation = db.fetch_one('''
                SELECT r.*, g.guest_id FROM reservations r 
                JOIN guests g ON r.guest_id = g.guest_id 
                WHERE r.reservation_id = ?
            ''', (reservation_id,))
            
            if not current_reservation:
                flash('Reservation not found!', 'error')
                return redirect(url_for('reservations'))
            
            # Check if room is available (excluding current reservation)
            if room_number != current_reservation['room_number']:
                room = db.fetch_one('SELECT * FROM rooms WHERE room_number = ? AND is_occupied = 0 AND clean = 1', (room_number,))
                if not room:
                    flash('Selected room is not available!', 'error')
                    return redirect(url_for('edit_reservation', reservation_id=reservation_id))
            
            # Check for date conflicts (excluding current reservation)
            conflicting_reservations = db.fetch_all('''
                SELECT * FROM reservations 
                WHERE room_number = ? 
                AND reservation_id != ?
                AND ((check_in <= ? AND check_out >= ?) OR (check_in <= ? AND check_out >= ?))
                AND is_checked_out = 0
            ''', (room_number, reservation_id, check_out_str, check_in_str, check_in_str, check_out_str))
            
            if conflicting_reservations:
                flash('Room is already booked for the selected dates!', 'error')
                return redirect(url_for('edit_reservation', reservation_id=reservation_id))
            
            # Get room details for price calculation
            room = db.fetch_one('SELECT * FROM rooms WHERE room_number = ?', (room_number,))
            
            # Calculate total amount
            nights = (check_out - check_in).days
            total_amount = nights * room['price']
            
            # Update guest information
            db.execute_query(
                'UPDATE guests SET name = ?, email = ?, phone = ?, address = ? WHERE guest_id = ?',
                (name, email, phone, address, current_reservation['guest_id'])
            )
            
            # Update reservation
            db.execute_query(
                '''UPDATE reservations 
                SET room_number = ?, check_in = ?, check_out = ?, total_amount = ? 
                WHERE reservation_id = ?''',
                (room_number, check_in.isoformat(), check_out.isoformat(), total_amount, reservation_id)
            )
            
            flash('Reservation updated successfully!', 'success')
            return redirect(url_for('view_reservation', reservation_id=reservation_id))
            
        except Exception as e:
            flash(f'Error updating reservation: {str(e)}', 'error')
            return redirect(url_for('edit_reservation', reservation_id=reservation_id))
    
    # GET request - show edit form
    try:
        reservation = db.fetch_one('''
            SELECT r.*, g.name as guest_name, g.email, g.phone, g.address, rm.room_type, rm.price
            FROM reservations r
            JOIN guests g ON r.guest_id = g.guest_id
            JOIN rooms rm ON r.room_number = rm.room_number
            WHERE r.reservation_id = ?
        ''', (reservation_id,))
        
        if not reservation:
            flash('Reservation not found!', 'error')
            return redirect(url_for('reservations'))
        
        available_rooms = db.fetch_all('SELECT * FROM rooms WHERE is_occupied = 0 AND clean = 1')
        return render_template('edit_reservation.html', reservation=reservation, rooms=available_rooms)
    except Exception as e:
        flash(f'Error loading reservation: {str(e)}', 'error')
        return redirect(url_for('reservations'))

@app.route('/check_in/<int:reservation_id>')
def check_in(reservation_id):
    """Check in a guest"""
    try:
        reservation = db.fetch_one('''
            SELECT r.*, rm.room_number FROM reservations r 
            JOIN rooms rm ON r.room_number = rm.room_number 
            WHERE r.reservation_id = ?
        ''', (reservation_id,))
        
        if not reservation:
            flash('Reservation not found!', 'error')
            return redirect(url_for('reservations'))
        
        if reservation['is_checked_in']:
            flash('Guest is already checked in!', 'error')
            return redirect(url_for('reservations'))
        
        # Update reservation and room status
        db.execute_query('UPDATE reservations SET is_checked_in = 1 WHERE reservation_id = ?', (reservation_id,))
        db.execute_query('UPDATE rooms SET is_occupied = 1 WHERE room_number = ?', (reservation['room_number'],))
        
        flash('Check-in successful!', 'success')
        return redirect(url_for('reservations'))
    except Exception as e:
        flash(f'Error during check-in: {str(e)}', 'error')
        return redirect(url_for('reservations'))

@app.route('/check_out/<int:reservation_id>')
def check_out(reservation_id):
    """Check out a guest"""
    try:
        reservation = db.fetch_one('''
            SELECT r.*, rm.room_number FROM reservations r 
            JOIN rooms rm ON r.room_number = rm.room_number 
            WHERE r.reservation_id = ?
        ''', (reservation_id,))
        
        if not reservation:
            flash('Reservation not found!', 'error')
            return redirect(url_for('reservations'))
        
        if not reservation['is_checked_in']:
            flash('Guest is not checked in!', 'error')
            return redirect(url_for('reservations'))
        
        if reservation['is_checked_out']:
            flash('Guest has already checked out!', 'error')
            return redirect(url_for('reservations'))
        
        # Update reservation and room status
        db.execute_query('UPDATE reservations SET is_checked_out = 1 WHERE reservation_id = ?', (reservation_id,))
        db.execute_query('UPDATE rooms SET is_occupied = 0, clean = 0 WHERE room_number = ?', (reservation['room_number'],))
        
        # Record payment
        db.execute_query(
            'INSERT INTO payments (reservation_id, amount, payment_method) VALUES (?, ?, ?)',
            (reservation_id, reservation['total_amount'], 'Cash/Card')
        )
        
        flash('Check-out successful!', 'success')
        return redirect(url_for('reservations'))
    except Exception as e:
        flash(f'Error during check-out: {str(e)}', 'error')
        return redirect(url_for('reservations'))

@app.route('/cancel_reservation/<int:reservation_id>')
def cancel_reservation(reservation_id):
    """Cancel or delete a reservation based on status"""
    try:
        print(f"DEBUG: Processing reservation {reservation_id}")
        
        reservation = db.fetch_one('SELECT * FROM reservations WHERE reservation_id = ?', (reservation_id,))
        
        if not reservation:
            flash('Reservation not found!', 'error')
            return redirect(url_for('reservations'))
        
        # Check if reservation is checked in
        if reservation['is_checked_in'] and not reservation['is_checked_out']:
            flash('Cannot cancel reservation - guest is currently checked in!', 'error')
            return redirect(url_for('reservations'))
        
        # Handle different reservation states
        if reservation['is_checked_out']:
            # For checked-out reservations, delete completely including payments
            db.execute_query('DELETE FROM payments WHERE reservation_id = ?', (reservation_id,))
            db.execute_query('DELETE FROM reservations WHERE reservation_id = ?', (reservation_id,))
            flash('Checked-out reservation deleted permanently!', 'success')
            print(f"DEBUG: Checked-out reservation {reservation_id} deleted permanently")
            
        else:
            # For regular reservations (not checked in), just cancel
            db.execute_query('DELETE FROM reservations WHERE reservation_id = ?', (reservation_id,))
            flash('Reservation cancelled successfully!', 'success')
            print(f"DEBUG: Reservation {reservation_id} cancelled")
        
        return redirect(url_for('reservations'))
        
    except Exception as e:
        error_msg = f'Error processing reservation: {str(e)}'
        print(f"DEBUG: {error_msg}")
        flash(error_msg, 'error')
        return redirect(url_for('reservations'))

@app.route('/mark_clean/<int:room_number>')
def mark_clean(room_number):
    """Mark room as cleaned"""
    try:
        room = db.fetch_one('SELECT * FROM rooms WHERE room_number = ?', (room_number,))
        if not room:
            flash('Room not found!', 'error')
            return redirect(url_for('rooms'))
        
        db.execute_query('UPDATE rooms SET clean = 1 WHERE room_number = ?', (room_number,))
        flash(f'Room {room_number} marked as cleaned!', 'success')
        return redirect(url_for('rooms'))
    except Exception as e:
        flash(f'Error marking room as clean: {str(e)}', 'error')
        return redirect(url_for('rooms'))

@app.route('/api/available_rooms')
def api_available_rooms():
    """API endpoint for available rooms"""
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    
    if not check_in or not check_out:
        return jsonify({'error': 'Missing dates'}), 400
    
    try:
        # FIXED DATETIME ERROR
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        
        # Find rooms that are not occupied during the requested period
        available_rooms = db.fetch_all('''
            SELECT * FROM rooms 
            WHERE room_number NOT IN (
                SELECT room_number FROM reservations 
                WHERE check_out > ? AND check_in < ? AND is_checked_out = 0
            )
            AND is_occupied = 0 AND clean = 1
        ''', (check_in_date.isoformat(), check_out_date.isoformat()))
        
        return jsonify(available_rooms)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

@app.route('/api/guests/search')
def api_search_guests():
    """API endpoint for guest search"""
    search_term = request.args.get('q', '')
    
    if not search_term:
        return jsonify([])
    
    guests_data = db.fetch_all('''
        SELECT * FROM guests 
        WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
        ORDER BY name
    ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
    
    return jsonify(guests_data)

@app.route('/api/guests/<int:guest_id>/reservations')
def api_guest_reservations(guest_id):
    """API endpoint for guest reservation history"""
    reservations_data = db.fetch_all('''
        SELECT r.*, rm.room_type 
        FROM reservations r 
        JOIN rooms rm ON r.room_number = rm.room_number 
        WHERE r.guest_id = ?
        ORDER BY r.created_date DESC
    ''', (guest_id,))
    
    return jsonify(reservations_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)