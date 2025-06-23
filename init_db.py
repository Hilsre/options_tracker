import sqlite3
import os

def get_db():
    """Datenbankverbindung herstellen"""
    db_path = os.environ.get('DATABASE_PATH', './db/options_tracker.db')
    
    # Stelle sicher, dass das Verzeichnis existiert
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Warte kurz falls die Datei gerade erstellt wird
    import time
    max_retries = 5
    for i in range(max_retries):
        try:
            conn = sqlite3.connect(db_path, timeout=30.0)
            conn.execute("PRAGMA foreign_keys = ON")  # Foreign Key Constraints aktivieren
            conn.execute("PRAGMA journal_mode = WAL")  # Bessere Parallelität
            conn.execute("PRAGMA synchronous = NORMAL")  # Bessere Performance
            return conn
        except sqlite3.OperationalError as e:
            if i < max_retries - 1:
                print(f"Datenbankverbindung fehlgeschlagen, Versuch {i+1}/{max_retries}...")
                time.sleep(1)
            else:
                raise e

def create_tables():
    """Alle Tabellen erstellen"""
    conn = get_db()
    
    try:
        # Basis Products Tabelle
        conn.execute("""
            CREATE TABLE IF NOT EXISTS basis_products (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # Product Types Tabelle
        conn.execute("""
            CREATE TABLE IF NOT EXISTS product_types (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # Directions Tabelle
        conn.execute("""
            CREATE TABLE IF NOT EXISTS directions (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # Strike Currencies Tabelle
        conn.execute("""
            CREATE TABLE IF NOT EXISTS strike_currencies (
                id INTEGER PRIMARY KEY,
                symbol TEXT UNIQUE NOT NULL
            )
        """)

        # Actions Tabelle
        conn.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # Products Tabelle
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                basis_product_id INTEGER NOT NULL,
                product_type_id INTEGER NOT NULL,
                direction_id INTEGER NOT NULL,
                strike REAL NOT NULL,
                strike_currency_id INTEGER NOT NULL,
                wkn TEXT,
                name TEXT,
                expiry_date DATE,
                FOREIGN KEY (basis_product_id) REFERENCES basis_products(id),
                FOREIGN KEY (product_type_id) REFERENCES product_types(id),
                FOREIGN KEY (direction_id) REFERENCES directions(id),
                FOREIGN KEY (strike_currency_id) REFERENCES strike_currencies(id)
            )
        """)

        # Transactions Tabelle
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

        # Settings Tabelle
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

        # Commit alle Änderungen
        conn.commit()
        print("✅ Tabellen erfolgreich erstellt")
        
        # Überprüfe, ob alle Tabellen erstellt wurden
        tables = ['basis_products', 'product_types', 'directions', 'strike_currencies', 'actions', 'products', 'transactions', 'settings']
        for table in tables:
            cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                raise Exception(f"Tabelle {table} wurde nicht erstellt")
        
        print("✅ Alle Tabellen erfolgreich verifiziert")
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Tabellen: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def fill_tables():
    """Basisdaten in die Tabellen einfügen"""
    conn = get_db()
    
    try:
        # Basis Products einfügen
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

        # Actions einfügen
        conn.execute("""
            INSERT OR IGNORE INTO actions (name) VALUES 
            ('buy'), 
            ('sell'), 
            ('rebuy'), 
            ('partial sell'), 
            ('redemption'), 
            ('knock-out')
        """)

        # Directions einfügen
        conn.execute("""
            INSERT OR IGNORE INTO directions (name) VALUES 
            ('Long'), 
            ('Short'), 
            ('Call'), 
            ('Put')
        """)

        # Product Types einfügen
        conn.execute("""
            INSERT OR IGNORE INTO product_types (name) VALUES 
            ('Knock-Out'), 
            ('Warrant'), 
            ('Factor')
        """)

        # Strike Currencies einfügen
        conn.execute("""
            INSERT OR IGNORE INTO strike_currencies (symbol) VALUES 
            ('€'), 
            ('$'), 
            ('Pkt.')
        """)

        # Default Settings einfügen
        conn.execute("""
            INSERT OR IGNORE INTO settings VALUES 
            ('default', 'en', 0.0, 'DD.MM.YYYY', 0.0, 0.0, 'Dark')
        """)

        conn.commit()
        print("✅ Basisdaten erfolgreich eingefügt")
        
    except sqlite3.Error as e:
        print(f"❌ Fehler beim Einfügen der Basisdaten: {e}")
        conn.rollback()
    finally:
        conn.close()

def check_database():
    """Überprüfe, ob die Datenbank korrekt initialisiert wurde"""
    conn = get_db()
    
    tables = [
        'basis_products', 'product_types', 'directions', 
        'strike_currencies', 'actions', 'products', 
        'transactions', 'settings'
    ]
    
    print("\n📊 Datenbank-Status:")
    print("-" * 40)
    
    for table in tables:
        try:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table:<20}: {count} Einträge")
        except sqlite3.Error as e:
            print(f"  {table:<20}: ❌ Fehler - {e}")
    
    conn.close()

def reset_database():
    """Datenbank komplett zurücksetzen (alle Tabellen löschen)"""
    conn = get_db()
    
    tables = [
        'transactions', 'products', 'settings', 'actions', 
        'strike_currencies', 'directions', 'product_types', 'basis_products'
    ]
    
    print("⚠️  Datenbank wird zurückgesetzt...")
    
    for table in tables:
        try:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  - Tabelle {table} gelöscht")
        except sqlite3.Error as e:
            print(f"  - Fehler beim Löschen von {table}: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Datenbank erfolgreich zurückgesetzt")

def init_database():
    """Komplette Datenbankinitialisierung"""
    print("🚀 Starte Datenbankinitialisierung...")
    
    # Tabellen erstellen
    create_tables()
    
    # Basisdaten einfügen
    fill_tables()
    
    # Status überprüfen
    check_database()
    
    print("\n✅ Datenbankinitialisierung abgeschlossen!")

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
            print("Verfügbare Befehle:")
            print("  python init_db.py        - Normale Initialisierung")
            print("  python init_db.py reset  - Datenbank zurücksetzen und neu initialisieren")
            print("  python init_db.py check  - Datenbankstatus überprüfen")
            print("  python init_db.py fill   - Nur Basisdaten einfügen")
    else:
        init_database()
