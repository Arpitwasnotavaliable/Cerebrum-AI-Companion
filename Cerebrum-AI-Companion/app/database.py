# app/database.py
import sqlite3
import os
from datetime import date

# --- Configuration ---
# This ensures the database file 'cerebrum.db' is created 
# right inside your 'app' folder, next to this script.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(APP_DIR, "cerebrum.db")
# ---------------------

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    # This line is a quality-of-life feature.
    # It makes the database return data as dictionary-like objects,
    # so we can access columns by name (e.g., row['content']).
    conn.row_factory = sqlite3.Row  
    return conn

def initialize_db():
    """
    Creates all necessary tables if they don't already exist.
    This function is the "blueprint" for our app's memory.
    """
    print("Initializing database...")
    # 'with' statement automatically handles closing the connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Table 1: Stores the chat history
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Table 2: Stores the habit definitions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL, -- 'user' or 'ai'
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Table 3: Stores a log of *when* habits were completed
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS HabitEntries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completion_date DATE NOT NULL,
            -- This is a key feature: If a habit is deleted from the 'Habits' table,
            -- all its log entries in *this* table are automatically deleted too.
            FOREIGN KEY (habit_id) REFERENCES Habits (id) ON DELETE CASCADE
        )
        """)
        
        conn.commit() # Saves all the changes
    print("Database initialized successfully.")

# --- Chat History Functions ---

def save_message(role, content):
    """Saves a single chat message to the database."""
    with get_db_connection() as conn:
        conn.execute("INSERT INTO Messages (role, content) VALUES (?, ?)", (role, content))
        conn.commit()

def get_messages():
    """Retrieves all messages from the database, oldest first."""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT role, content FROM Messages ORDER BY timestamp ASC")
        return cursor.fetchall()

# --- Habit Functions ---

def add_habit(habit_title, source="user"):
    """Adds a new habit to the tracker."""
    with get_db_connection() as conn:
        conn.execute("INSERT INTO Habits (title, source) VALUES (?, ?)", (habit_title, source))
        conn.commit()
        print(f"Habit added to DB: {habit_title}")

def get_habits():
    """Retrieves all current habits."""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT id, title, source FROM Habits ORDER BY created_at DESC")
        return cursor.fetchall()

def update_habit(habit_id, new_title):
    """Updates the text of an existing habit."""
    with get_db_connection() as conn:
        conn.execute("UPDATE Habits SET title = ? WHERE id = ?", (new_title, habit_id))
        conn.commit()

def delete_habit(habit_id):
    """Deletes a habit and all its associated log entries."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM Habits WHERE id = ?", (habit_id,))
        conn.commit()

# --- Habit Logging Functions ---

def log_habit(habit_id, completion_date_str):
    """Logs a habit as complete for a specific date."""
    with get_db_connection() as conn:
        # Check if it's already logged for that day to prevent duplicates
        exists = conn.execute(
            "SELECT 1 FROM HabitEntries WHERE habit_id = ? AND completion_date = ?",
            (habit_id, completion_date_str)
        ).fetchone()
        
        if not exists:
            conn.execute("INSERT INTO HabitEntries (habit_id, completion_date) VALUES (?, ?)",
                         (habit_id, completion_date_str))
            conn.commit()

def unlog_habit(habit_id, completion_date_str):
    """Removes a habit log for a specific date."""
    with get_db_connection() as conn:
        conn.execute(
            "DELETE FROM HabitEntries WHERE habit_id = ? AND completion_date = ?",
            (habit_id, completion_date_str)
        )
        conn.commit()

def get_habit_entries(habit_id):
    """Retrieves all completion dates for a specific habit."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT completion_date FROM HabitEntries WHERE habit_id = ? ORDER BY completion_date DESC",
            (habit_id,)
        )
        # Return a simple list of date strings
        return [row['completion_date'] for row in cursor.fetchall()]

def get_habits_with_today_status(today_date_str):
    """Gets all habits and checks if they are completed today."""
    with get_db_connection() as conn:
        query = """
        SELECT 
            h.id, 
            h.title, 
            EXISTS (
                SELECT 1 FROM HabitEntries he 
                WHERE he.habit_id = h.id AND he.completion_date = ?
            ) as completed_today
        FROM Habits h
        ORDER BY h.created_at DESC
        """
        cursor = conn.execute(query, (today_date_str,))
        return cursor.fetchall()

# --- Privacy Function ---

def clear_all_data():
    """
    DELETES ALL USER DATA FROM THE DATABASE.
    This is the function for the "Clear All App Data" button.
    """
    print("WARNING: Clearing all user data.")
    with get_db_connection() as conn:
        # We only need to delete from the main tables.
        # 'HabitEntries' rows are deleted automatically because of the
        # 'ON DELETE CASCADE' rule we added to that table.
        conn.execute("DELETE FROM Messages")
        conn.execute("DELETE FROM Habits")
        conn.commit()
    print("All app data has been cleared.")

# --- Auto-Initialize ---
# This bit of code at the end is a clever trick.
# It makes the 'initialize_db' function run *one time*
# when our application first starts and imports this file.
# This ensures the database and tables always exist *before*
# we try to use them.
if __name__ != "__main__":
    initialize_db()