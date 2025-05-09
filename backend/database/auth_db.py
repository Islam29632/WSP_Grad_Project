import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional


class AuthDB:
    def __init__(self, db_path: str = os.path.join(os.path.dirname(__file__), "auth.db")):
        """Initialize the database connection"""
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hashed TEXT NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create activity_logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

        conn.commit()
        conn.close()

    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username: str, password: str) -> bool:
        """Register a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Hash the password before storing
            hashed_password = self._hash_password(password)

            # Insert new user
            cursor.execute(
                'INSERT INTO users (username, password_hashed) VALUES (?, ?)',
                (username, hashed_password)
            )

            # Get the user_id of the newly created user
            user_id = cursor.lastrowid

            # Log the registration activity
            cursor.execute(
                'INSERT INTO activity_logs (user_id, action) VALUES (?, ?)',
                (user_id, 'user_registration')
            )

            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Username already exists
            return False
        finally:
            conn.close()

    def verify_user(self, username: str, password: str) -> Optional[int]:
        """Verify user credentials and return user_id if valid"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT user_id, password_hashed FROM users WHERE username = ?',
            (username,)
        )
        result = cursor.fetchone()

        if result and result[1] == self._hash_password(password):
            user_id = result[0]
            # Log the successful login
            cursor.execute(
                'INSERT INTO activity_logs (user_id, action) VALUES (?, ?)',
                (user_id, 'user_login')
            )
            conn.commit()
            conn.close()
            return user_id

        conn.close()
        return None

    def log_activity(self, user_id: int, action: str):
        """Log user activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO activity_logs (user_id, action) VALUES (?, ?)',
            (user_id, action)
        )

        conn.commit()
        conn.close()

    def get_user_activities(self, user_id: int) -> list:
        """Get all activities for a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            '''SELECT action, timestamp 
               FROM activity_logs 
               WHERE user_id = ? 
               ORDER BY timestamp DESC''',
            (user_id,)
        )
        activities = cursor.fetchall()

        conn.close()
        return activities
