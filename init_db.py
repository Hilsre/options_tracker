#!/usr/bin/env python3
"""
Database Initialization Script für Options Tracker
Erstellt die notwendigen Tabellen falls sie nicht existieren
"""

import sqlite3
import os
from pathlib import Path

# Datenbankpfad aus Environment Variable oder Default
DB_PATH = os.getenv('DATABASE_PATH', '/app/data/options_tracker.db')

def init_database():
    """Initialisiert die Datenbank mit allen notwendigen Tabellen"""
    
    # Stelle sicher, dass das Verzeichnis existiert
    db_dir = Path(DB_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Initialisiere Datenbank: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Schema Version Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Produkte/Instrumente Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instruments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isin TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                instrument_type TEXT NOT NULL,
                underlying TEXT,
                strike_price REAL,
                expiry_date DATE,
                barrier REAL,
                leverage REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transaktionen Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                transaction_date DATE NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_unit REAL NOT NULL,
                total_amount REAL NOT NULL,
                fees REAL DEFAULT 0,
                tax REAL DEFAULT 0,
                broker TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (instrument_id) REFERENCES instruments (id)
            )
        ''')
        
        # Positionen Tabelle (für FIFO-Berechnungen)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                avg_price REAL NOT NULL,
                total_invested REAL NOT NULL,
                realized_pnl REAL DEFAULT 0,
                unrealized_pnl REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (instrument_id) REFERENCES instruments (id)
            )
        ''')
        
        # Steuerliche Ereignisse Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tax_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                tax_year INTEGER NOT NULL,
                realized_gain_loss REAL NOT NULL,
                tax_base REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        ''')
        
        # Indizes für bessere Performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (transaction_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_instrument ON transactions (instrument_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_instruments_isin ON instruments (isin)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tax_events_year ON tax_events (tax_year)')
        
        # Prüfe ob Schema Version existiert, wenn nicht setze auf 1
        cursor.execute('SELECT COUNT(*) FROM schema_version')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO schema_version (version) VALUES (1)')
            print("Schema Version auf 1 gesetzt")
        
        conn.commit()
        print("Datenbank erfolgreich initialisiert")
        
        # Debug: Zeige verfügbare Tabellen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Verfügbare Tabellen: {[table[0] for table in tables]}")
        
    except Exception as e:
        print(f"Fehler bei der Datenbankinitialisierung: {e}")
        raise
    finally:
        conn.close()

def check_database_health():
    """Prüft die Gesundheit der Datenbank"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Prüfe ob alle Tabellen existieren
        required_tables = ['instruments', 'transactions', 'positions', 'tax_events', 'schema_version']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = set(required_tables) - set(existing_tables)
        if missing_tables:
            print(f"Fehlende Tabellen: {missing_tables}")
            return False
        
        print("Datenbankgesundheit: OK")
        return True
        
    except Exception as e:
        print(f"Fehler bei Datenbankprüfung: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== Options Tracker DB Initialisierung ===")
    init_database()
    
    if check_database_health():
        print("✅ Datenbank bereit für Streamlit")
    else:
        print("❌ Datenbankprobleme erkannt")
        exit(1)
