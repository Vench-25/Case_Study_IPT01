"""
Database initialization script.
Reads schema.sql and creates the database tables.
Does NOT overwrite an existing database — it uses CREATE TABLE IF NOT EXISTS.
"""
import os
import sqlite3
import sys

def init_db():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_dir = os.path.join(base_dir, 'database')
    db_path = os.path.join(db_dir, 'event_system.db')
    schema_path = os.path.join(base_dir, 'schema.sql')


    os.makedirs(db_dir, exist_ok=True)

    if not os.path.exists(schema_path):
        print(f"Error: schema.sql not found at {schema_path}")
        sys.exit(1)


    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()


    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON')
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print(f"Database initialized successfully at: {db_path}")
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
