import sqlite3
from pathlib import Path
import shutil

DB_DIR = Path("db")
DB_FILE = DB_DIR / "options_tracker.db"
DEFAULT_DB_TEMPLATE = Path("db/options_tracker.db")

CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS settings (
        user_id TEXT PRIMARY KEY,
        language_code TEXT DEFAULT 'en',
        tax_rate REAL DEFAULT 0.26,
        date_format TEXT DEFAULT 'DD.MM.YYYY'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS basis_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS product_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS directions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS strike_currencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        basis_product_id INTEGER,
        product_type_id INTEGER,
        direction_id INTEGER,
        strike REAL,
        strike_currency_id INTEGER,
        wkn TEXT,
        name TEXT,
        expiry_date TEXT,
        FOREIGN KEY (basis_product_id) REFERENCES basis_products(id),
        FOREIGN KEY (product_type_id) REFERENCES product_types(id),
        FOREIGN KEY (direction_id) REFERENCES directions(id),
        FOREIGN KEY (strike_currency_id) REFERENCES strike_currencies(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER,
        date TEXT,
        product_id INTEGER,
        price REAL,
        qty INTEGER,
        fee REAL,
        tax REAL,
        total_price REAL,
        price_correct INTEGER,
        action_id INTEGER,
        open_qty INTEGER,
        gain REAL
    )
    """
]

def setup_database():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    if DB_FILE.exists():
        return

    if DEFAULT_DB_TEMPLATE.exists():
        shutil.copy(DEFAULT_DB_TEMPLATE, DB_FILE)
    else:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for stmt in CREATE_TABLES_SQL:
            cursor.execute(stmt)
        conn.commit()
        conn.close()

if __name__ == "__main__":
    setup_database()
