import sqlite3
import os

def get_db():
    db_path = os.environ.get('DATABASE_PATH', './data/options_tracker.db')
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON") 
    return conn

def create_tables():
    conn = get_db()
    
    # Basis Products Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS basis_products (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Product Types Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS product_types (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Directions Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS directions (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Strike Currencies Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS strike_currencies (
            id INTEGER PRIMARY KEY,
            symbol TEXT UNIQUE NOT NULL
        )
    """)

    # Actions Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Products Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            basis_product_id INTEGER NOT NULL,
            product_type_id INTEGER NOT NULL,
            direction_id INTEGER NOT NULL,
            strike REAL NOT NULL,
            strike_currency_id INTEGER NOT NULL,
            wkn TEXT UNIQUE,
            name TEXT,
            expiry_date DATE,
            FOREIGN KEY (basis_product_id) REFERENCES basis_products(id),
            FOREIGN KEY (product_type_id) REFERENCES product_types(id),
            FOREIGN KEY (direction_id) REFERENCES directions(id),
            FOREIGN KEY (strike_currency_id) REFERENCES strike_currencies(id)
        )
    """)

    # Transactions Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            trade_id INTEGER NOT NULL,
            date DATE NOT NULL,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL,
            qty INTEGER NOT NULL,
            fee INTEGER DEFAULT 1,
            tax REAL DEFAULT 0.0,
            total_price REAL NOT NULL,
            gain REAL DEFAULT 0,
            price_correct INTEGER DEFAULT 1,
            action_id INTEGER NOT NULL,
            open_qty INTEGER,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (action_id) REFERENCES actions(id)
        )
    """)

    # Settings Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            user_id TEXT PRIMARY KEY,
            language_code TEXT DEFAULT 'en',
            tax_rate REAL DEFAULT 0.0,
            date_format TEXT DEFAULT 'DD.MM.YYYY',
            tax_allowance REAL DEFAULT 0.0,
            loss_carryforward REAL DEFAULT 0.0,
            theme_mode TEXT DEFAULT 'Dark'
        )
    """)

    conn.commit()
    conn.close()

def fill_tables():
    conn = get_db()
    
    try:
        conn.execute("""
            INSERT OR IGNORE INTO basis_products (name) VALUES 
            ('Rheinmetall AG'), 
            ('Renk Group'), 
            ('DAX'), 
            ('S&P500'), 
            ('Nasdaq'), 
            ('Nvidia'), 
            ('Apple'), 
            ('Amazon'), 
            ('Meta'), 
            ('Hensoldt AG'), 
            ('Thyssenkrupp AG'), 
            ('Coinbase')
        """)

        conn.execute("""
            INSERT OR IGNORE INTO actions (name) VALUES 
            ('buy'), 
            ('sell'), 
            ('rebuy'), 
            ('partial sell'), 
            ('redemption'), 
            ('knock-out')
        """)

        conn.execute("""
            INSERT OR IGNORE INTO directions (name) VALUES 
            ('Long'), 
            ('Short'), 
            ('Call'), 
            ('Put')
        """)

        conn.execute("""
            INSERT OR IGNORE INTO product_types (name) VALUES 
            ('Knock-Out'), 
            ('Warrant'), 
            ('Factor')
        """)

        conn.execute("""
            INSERT OR IGNORE INTO strike_currencies (symbol) VALUES 
            ('€'), 
            ('$'), 
            ('Pkt.')
        """)

        conn.execute("""
            INSERT OR IGNORE INTO settings VALUES 
            ('default', 'en', 0.0, 'DD.MM.YYYY', 0.0, 0.0, 'Dark')
        """)

        conn.commit()
        
    except sqlite3.Error as e:
        conn.rollback()
    finally:
        conn.close()

def check_database():
    conn = get_db()
    
    tables = [
        'basis_products', 'product_types', 'directions', 
        'strike_currencies', 'actions', 'products', 
        'transactions', 'settings'
    ]
    
    
    for table in tables:
        try:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table:<20}: {count} Entries")
        except sqlite3.Error as e:
            print(f"  {table:<20}: ❌ Error - {e}")
    
    conn.close()

def reset_database():
    conn = get_db()
    
    tables = [
        'transactions', 'products', 'settings', 'actions', 
        'strike_currencies', 'directions', 'product_types', 'basis_products'
    ]
    
    
    for table in tables:
        try:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  - Tabelle {table} gelöscht")
        except sqlite3.Error as e:
            print(f"  - Error while deleting {table}: {e}")
    
    conn.commit()
    conn.close()

def init_database():
    create_tables()
    fill_tables()
    check_database()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset":
            reset_database()
            init_database()
        elif sys.argv[1] == "check":
            check_database()
        elif sys.argv[1] == "fill":
            fill_tables()
        else:
            print("Available options:")
            print("  python init_db.py)
            print("  python init_db.py reset")
            print("  python init_db.py check")
            print("  python init_db.py fill")
    else:
        init_database()
