import sqlite3
import json
import os
import werkzeug.security

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_to_multitenant(conn):
    cursor = conn.cursor()
    
    # 1. Migrate people table to add user_id and remove unique(name) global constraint
    cursor.execute("PRAGMA table_info(people)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "user_id" not in columns:
        print("Migration: Upgrading 'people' table to support multi-tenancy...")
        try:
            # Rename existing table
            cursor.execute("ALTER TABLE people RENAME TO people_old")
            
            # Create new table
            cursor.execute("""
            CREATE TABLE people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                email TEXT,
                whatsapp_number TEXT,
                UNIQUE(user_id, name)
            )""")
            
            # Copy old data, assigning default user_id = 1
            cursor.execute("""
            INSERT INTO people (id, name, email, whatsapp_number, user_id)
            SELECT id, name, email, whatsapp_number, 1 FROM people_old
            """)
            
            # Drop old table
            cursor.execute("DROP TABLE people_old")
            print("Migration: Successfully upgraded 'people' table.")
        except Exception as e:
            print(f"Migration error on 'people' table: {e}")
            
    # 2. Migrate delivery_history table to add user_id
    cursor.execute("PRAGMA table_info(delivery_history)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "user_id" not in columns:
        print("Migration: Upgrading 'delivery_history' table to support multi-tenancy...")
        try:
            cursor.execute("ALTER TABLE delivery_history ADD COLUMN user_id INTEGER DEFAULT 1")
            print("Migration: Successfully upgraded 'delivery_history' table.")
        except Exception as e:
            print(f"Migration error on 'delivery_history' table: {e}")

    # 3. Migrate photos table to add event_confidence and event_occasion
    cursor.execute("PRAGMA table_info(photos)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "event_confidence" not in columns:
        print("Migration: Upgrading 'photos' table with 'event_confidence' column...")
        try:
            cursor.execute("ALTER TABLE photos ADD COLUMN event_confidence REAL DEFAULT 1.0")
            print("Migration: Successfully added 'event_confidence' column.")
        except Exception as e:
            print(f"Migration error adding 'event_confidence': {e}")
            
    if "event_occasion" not in columns:
        print("Migration: Upgrading 'photos' table with 'event_occasion' column...")
        try:
            cursor.execute("ALTER TABLE photos ADD COLUMN event_occasion TEXT DEFAULT 'Non_Occasion'")
            print("Migration: Successfully added 'event_occasion' column.")
        except Exception as e:
            print(f"Migration error adding 'event_occasion': {e}")

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users table (Auth)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )""")
    
    # 2. People table (Contacts / Person Profiles)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        email TEXT,
        whatsapp_number TEXT,
        UNIQUE(user_id, name)
    )""")
    
    # 3. Photos table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        public_id TEXT,
        secure_url TEXT,
        original_filename TEXT,
        upload_date TEXT,
        recognized_person TEXT,
        created_at TEXT,
        event TEXT DEFAULT 'General',
        event_confidence REAL DEFAULT 1.0,
        event_occasion TEXT DEFAULT 'Non_Occasion'
    )""")
    
    # 4. Faces table (detected faces, bounding boxes, embeddings)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        photo_id INTEGER,
        label TEXT DEFAULT 'Unknown',
        embedding TEXT,
        x INTEGER,
        y INTEGER,
        w INTEGER,
        h INTEGER,
        FOREIGN KEY(photo_id) REFERENCES photos(id) ON DELETE CASCADE
    )""")
    
    # 5. Delivery History table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS delivery_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        timestamp TEXT,
        delivery_method TEXT,
        recipient TEXT,
        photo_ids TEXT,
        status TEXT,
        details TEXT
    )""")
    
    # Run migrations on existing schemas if needed
    migrate_to_multitenant(conn)
    
    # Insert default admin user if not exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed_password = werkzeug.security.generate_password_hash("admin123")
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", hashed_password))
        
    # Insert initial mock contact people for admin (user_id = 1) if not exists
    mock_contacts = [
        ("Mom", "mom.sharma@gmail.com", "+919876543210"),
        ("Dad", "dad.sharma@gmail.com", "+919000011111"),
        ("Rahul", "rahul.dev@gmail.com", "+919988776655"),
        ("Priya", "priya.sen@gmail.com", "+919123456789")
    ]
    
    for name, email, wa in mock_contacts:
        cursor.execute("SELECT id FROM people WHERE user_id = 1 AND name = ?", (name,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO people (user_id, name, email, whatsapp_number) VALUES (1, ?, ?, ?)", (name, email, wa))
            
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
