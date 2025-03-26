import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import pytz

# Database file path
DB_PATH = Path(__file__).parent.parent / "data"
DB_FILE = DB_PATH / "canvasbot.db"

# Ensure the data directory exists
DB_PATH.mkdir(exist_ok=True)

# Original JSON database file
JSON_DB_FILE = DB_PATH / "users.json"


class Database:
    """SQLite database for storing user data."""
    
    def __init__(self):
        """Initialize the database connection and create tables if they don't exist."""
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        
        # Migrate data from JSON if needed and if the JSON file exists
        if JSON_DB_FILE.exists() and self.is_empty():
            self.migrate_from_json()
    
    def connect(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(DB_FILE)
        # Enable dictionary access to rows
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """Create the necessary tables if they don't exist."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                canvas_token TEXT,
                endpoint TEXT,
                daily BOOLEAN DEFAULT 1,
                ping BOOLEAN DEFAULT 1,
                dm BOOLEAN DEFAULT 1,
                starred BOOLEAN DEFAULT 0,
                muted_until TEXT DEFAULT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def is_empty(self):
        """Check if the users table is empty."""
        self.cursor.execute("SELECT COUNT(*) FROM users")
        count = self.cursor.fetchone()[0]
        return count == 0
    
    def migrate_from_json(self):
        """Migrate data from the JSON database to SQLite."""
        try:
            with open(JSON_DB_FILE, 'r') as f:
                json_data = json.load(f)
                
            # Insert each user from the JSON file
            for user_id, user_data in json_data.items():
                self.cursor.execute('''
                    INSERT INTO users 
                    (user_id, canvas_token, endpoint, daily, ping, dm, starred, muted_until)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    user_data.get('id'),
                    user_data.get('endpoint'),
                    user_data.get('daily', True),
                    user_data.get('ping', True),
                    user_data.get('dm', True),
                    user_data.get('starred', False),
                    user_data.get('muted_until')
                ))
            
            self.conn.commit()
            print(f"Successfully migrated {len(json_data)} users from JSON to SQLite database.")
            
            # Create a backup of the JSON file
            backup_file = str(JSON_DB_FILE) + ".backup"
            with open(backup_file, 'w') as f:
                json.dump(json_data, f, indent=4)
            
            print(f"Created backup of original JSON data at {backup_file}")
        
        except Exception as e:
            print(f"Error migrating from JSON: {e}")
    
    def __contains__(self, key):
        """Check if a user exists in the database."""
        self.cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (str(key),))
        return self.cursor.fetchone() is not None
    
    def __getitem__(self, key):
        """Get a user's data from the database."""
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (str(key),))
        row = self.cursor.fetchone()
        
        if row:
            # Convert SQLite row to dictionary
            user_data = dict(row)
            
            # Map keys to match the old JSON format
            result = {
                'id': user_data['canvas_token'],
                'endpoint': user_data['endpoint'],
                'daily': bool(user_data['daily']),
                'ping': bool(user_data['ping']),
                'dm': bool(user_data['dm']),
                'starred': bool(user_data['starred']),
            }
            
            # Add muted_until only if it exists
            if user_data['muted_until']:
                result['muted_until'] = user_data['muted_until']
                
            return result
        return None
    
    def __setitem__(self, key, value):
        """Set or update a user's data in the database."""
        user_id = str(key)
        now = datetime.now(pytz.UTC).isoformat()
        
        # Check if user exists
        if user_id in self:
            # Update existing user
            self.cursor.execute('''
                UPDATE users SET
                canvas_token = ?,
                endpoint = ?,
                daily = ?,
                ping = ?,
                dm = ?,
                starred = ?,
                muted_until = ?,
                updated_at = ?
                WHERE user_id = ?
            ''', (
                value.get('id'),
                value.get('endpoint'),
                value.get('daily', True),
                value.get('ping', True),
                value.get('dm', True),
                value.get('starred', False),
                value.get('muted_until'),
                now,
                user_id
            ))
        else:
            # Insert new user
            self.cursor.execute('''
                INSERT INTO users
                (user_id, canvas_token, endpoint, daily, ping, dm, starred, muted_until, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                value.get('id'),
                value.get('endpoint'),
                value.get('daily', True),
                value.get('ping', True),
                value.get('dm', True),
                value.get('starred', False),
                value.get('muted_until'),
                now,
                now
            ))
        
        self.conn.commit()
    
    def keys(self):
        """Get all user IDs in the database."""
        self.cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in self.cursor.fetchall()]


# Initialize the database
db = Database()
