import os
import json
from pathlib import Path

# Database file path
DB_FILE = Path(__file__).parent.parent / "data" / "users.json"

# Ensure the data directory exists
Path(DB_FILE.parent).mkdir(exist_ok=True)

class Database:
    """A simple JSON-based database for storing user data."""
    
    def __init__(self):
        self.data = {}
        self.load()
    
    def load(self):
        """Load data from the database file."""
        if DB_FILE.exists():
            try:
                with open(DB_FILE, 'r') as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                self.data = {}
                self.save()  # Create a new empty database file
        else:
            self.save()  # Create a new empty database file
    
    def save(self):
        """Save data to the database file."""
        with open(DB_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)
    
    def __contains__(self, key):
        """Check if a key exists in the database."""
        return str(key) in self.data
    
    def __getitem__(self, key):
        """Get a value from the database."""
        return self.data.get(str(key), None)
    
    def __setitem__(self, key, value):
        """Set a value in the database."""
        self.data[str(key)] = value
        self.save()
    
    def keys(self):
        """Get all keys in the database."""
        return self.data.keys()
    
    def values(self):
        """Get all values in the database."""
        return self.data.values()
    
    def items(self):
        """Get all items in the database."""
        return self.data.items()
    
    def get(self, key, default=None):
        """Get a value from the database with a default fallback."""
        return self.data.get(str(key), default)

# Create a database instance
db = Database()
