import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional

class PostgreSQLDatabase:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host="localhost",
                database="head_mouse_VA_db",
                user="postgres",
                password="postgres",
                port="5432"
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("Successfully connected to PostgreSQL")
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            raise

    def create_tables(self):
        try:
            # Users table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE
                )
            """)
            
            # Faces table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS faces (
                    face_id TEXT PRIMARY KEY,
                    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
                    face_data BYTEA NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User settings table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    setting_id TEXT PRIMARY KEY,
                    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
                    smoothing FLOAT DEFAULT 0.9,
                    amplification FLOAT DEFAULT 6.5
                    
                )
            """)
            
            self.conn.commit()
            print("Tables created successfully")
        except Exception as e:
            print(f"Error creating tables: {e}")
            self.conn.rollback()
            raise

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Create a singleton instance
db = PostgreSQLDatabase()
