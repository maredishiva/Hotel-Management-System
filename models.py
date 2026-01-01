import sqlite3
import datetime
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
                (101, "Standard Single", 5000, 1, 0, 1, "Cozy room with single bed"),
                (102, "Standard Double", 7500, 2, 0, 1, "Comfortable room with double bed"),
                (103, "Deluxe Suite", 15000, 4, 0, 1, "Spacious suite with living area"),
                (201, "Standard Single", 5000, 1, 0, 1, "Cozy room with single bed"),
                (202, "Standard Double", 7500, 2, 0, 1, "Comfortable room with double bed"),
                (203, "Executive Suite", 20000, 3, 0, 1, "Luxurious suite with premium amenities")
            ]
            cursor.executemany(
                "INSERT INTO rooms (room_number, room_type, price, capacity, is_occupied, clean, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                sample_rooms
            )
        
        conn.commit()
        conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL query and return cursor"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        """Fetch all results from query"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Fetch single result from query"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None