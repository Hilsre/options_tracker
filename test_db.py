#!/usr/bin/env python3
"""
Dieses Script testet die Datenbankverbindung und führt den SQL-Query aus,
der in der Streamlit-App fehlschlägt.
"""

import sqlite3
import os
import sys

def test_database_connection():
    """Teste die Datenbankverbindung und die problematische Query"""
    
    db_path = os.environ.get('DATABASE_PATH', './data/options_tracker.db')
    
    print(f"🔍 Teste Datenbankverbindung zu: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbankdatei existiert nicht: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Liste aller Tabellen
        print("\n📊 Vorhandene Tabellen:")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  ✓ {table[0]}")
        
        # Teste jede Tabelle einzeln
        expected_tables = ['basis_products', 'product_types', 'directions', 'strike_currencies', 'actions', 'products', 'transactions', 'settings']
        
        print("\n🔍 Prüfe erwartete Tabellen:")
        missing_tables = []
        for table in expected_tables:
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✓ {table}: {count} Einträge")
            except sqlite3.OperationalError as e:
                print(f"  ❌ {table}: {e}")
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n❌ Fehlende Tabellen: {missing_tables}")
            return False
        
        # Teste die problematische Query aus der Streamlit-App
        print("\n🧪 Teste die problematische SQL-Query:")
        test_query = """
        SELECT t.id as transaction_id, 
               t.trade_id AS "Trade ID", 
               t.date, 
               t.price, 
               t.qty, 
               t.fee, 
               t.tax, 
               t.total_price, 
               t.gain, 
               t.open_qty AS open_qty, 
               p.name as product_name, 
               p.wkn, 
               p.strike, 
               p.expiry_date, 
               bp.name as basis_product, 
               pt.name as product_type, 
               d.name as direction, 
               sc.symbol as strike_currency, 
               a.name as action, 
               d.name || '@' || CAST(p.strike AS TEXT) || sc.symbol || ' ' || bp.name AS name 
        FROM transactions t 
        JOIN products p ON t.product_id = p.id 
        JOIN basis_products bp ON p.basis_product_id = bp.id 
        JOIN product_types pt ON p.product_type_id = pt.id 
        JOIN directions d ON p.direction_id = d.id 
        JOIN strike_currencies sc ON p.strike_currency_id = sc.id 
        JOIN actions a ON t.action_id = a.id 
        ORDER BY t.date DESC
        """
        
        try:
            cursor = conn.execute(test_query)
            results = cursor.fetchall()
            print(f"  ✅ Query erfolgreich ausgeführt! {len(results)} Ergebnisse gefunden.")
        except sqlite3.Error as e:
            print(f"  ❌ Query fehlgeschlagen: {e}")
            return False
        
        conn.close()
        print("\n✅ Alle Datenbanktests erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Datenbankfehler: {e}")
        return False

def wait_for_database():
    """Warte bis die Datenbank vollständig initialisiert ist"""
    import time
    
    max_retries = 30  # 30 Sekunden warten
    retry_interval = 1  # Jede Sekunde prüfen
    
    print("⏳ Warte auf vollständige Datenbankinitialisierung...")
    
    for i in range(max_retries):
        if test_database_connection():
            print(f"✅ Datenbank nach {i+1} Sekunden bereit!")
            return True
        
        if i < max_retries - 1:
            print(f"  🔄 Versuch {i+1}/{max_retries} - warte {retry_interval}s...")
            time.sleep(retry_interval)
    
    print("❌ Timeout: Datenbank nicht rechtzeitig bereit!")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "wait":
        success = wait_for_database()
        sys.exit(0 if success else 1)
    else:
        success = test_database_connection()
        sys.exit(0 if success else 1)
