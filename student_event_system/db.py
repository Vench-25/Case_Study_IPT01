"""
Database connection utilities for NEUST-TOC Student Event System.
Separated to prevent circular imports between app.py and route blueprints.
"""
import sqlite3
from flask import g, current_app
from config import Config


def get_db():
    """Get database connection for current request context."""
    if 'db' not in g:
        db_path = current_app.config.get('DATABASE', Config.DATABASE)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

