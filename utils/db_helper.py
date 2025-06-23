import os
import sqlite3
import streamlit as st
import logging

def get_db():
    """
    Robuste Datenbankverbindungsfunktion, die verschiedene Pfade ausprobiert
    und sowohl in lokaler Entwicklung als auch in Docker-Containern funktioniert.
    """
    
    # Liste möglicher Datenbankpfade (in Prioritätsreihenfolge)
    possible_paths = [
        # Docker-Container Pfade
        "/app/db/options_tracker.db",
        "/app/options_tracker.db", 
        "./db/options_tracker.db",
        "./options_tracker.db",
        "/app/data/options_tracker.db",
        
        # Relative Pfade basierend auf aktueller Datei
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "db", "options_tracker.db"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "options_tracker.db"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "options_tracker.db"),
        
        # Pfade basierend auf Working Directory
        os.path.join(os.getcwd(), "db", "options_tracker.db"),
        os.path.join(os.getcwd(), "options_tracker.db"),
        
        # Root-Level Suche
        os.path.join("/", "db", "options_tracker.db"),
    ]
    
    # Durchsuche alle möglichen Pfade
    for db_path in possible_paths:
        try:
            # Normalisiere den Pfad
            normalized_path = os.path.normpath(db_path)
            
            # Prüfe ob die Datei existiert
            if os.path.exists(normalized_path):
                # Teste die Verbindung
                conn = sqlite3.connect(normalized_path)
                conn.row_factory = sqlite3.Row
                
                # Teste ob es eine gültige SQLite-Datenbank ist
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                if tables:  # Wenn Tabellen vorhanden sind
                    logging.info(f"Datenbankverbindung erfolgreich: {normalized_path}")
                    return conn
                else:
                    conn.close()
                    logging.warning(f"Datenbank gefunden aber leer: {normalized_path}")
                    
        except Exception as e:
            logging.debug(f"Fehler bei Pfad {db_path}: {str(e)}")
            continue
    
    # Wenn keine existierende Datenbank gefunden wurde, erstelle eine neue
    # Bevorzuge Docker-Container Pfad wenn wir in einem Container sind
    if os.path.exists('/app'):
        default_path = "/app/db/options_tracker.db"
        os.makedirs("/app/db", exist_ok=True)
    else:
        default_path = os.path.join(os.getcwd(), "db", "options_tracker.db")
        os.makedirs(os.path.join(os.getcwd(), "db"), exist_ok=True)
    
    try:
        logging.info(f"Erstelle neue Datenbank: {default_path}")
        conn = sqlite3.connect(default_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"Fehler beim Erstellen der Datenbank: {str(e)}")
        raise Exception(f"Konnte keine Datenbankverbindung herstellen: {str(e)}")


def get_options(query):
    conn = get_db()
    return [tuple(row) for row in conn.execute(query).fetchall()]


def new_transaction(**kwargs):
    conn = get_db()
    sql = """
    INSERT INTO transactions (
        trade_id, date, product_id, price, qty, fee, tax, total_price, price_correct, action_id, open_qty, gain
    ) VALUES (
        ?,?,?,?,?,?,?,?,?,?,?,?
    )
    """

    values = (
        kwargs["trade_id"],
        kwargs["date"],
        kwargs["product_id"],
        kwargs["price"],
        kwargs["qty"],
        kwargs["fee"],
        kwargs["tax"],
        kwargs["total_price"],
        kwargs["price_correct"],
        kwargs["action_id"],
        kwargs["open_qty"],
        kwargs["gain"]
    )

    conn.execute(sql, values)
    conn.commit()


def get_product_choices():
    conn = get_db()
    return [
        (row["trade_id"], f"{row['direction']} @ {row['strike']}{row['currency']} {row['basis_name']}",
         row["open_qty"], row["product_id"], row["price_paid"])
        for row in conn.execute("""           
        SELECT
            t.trade_id,
            p.id AS product_id,
            bp.name AS basis_name,
            pt.name AS type_name,
            d.name AS direction,
            p.strike,
            sc.symbol AS currency,
            SUM(COALESCE(t.open_qty,0)) AS open_qty,
            SUM(COALESCE(t.total_price,0)) AS price_paid
        FROM transactions t
        JOIN products p ON t.product_id = p.id
        JOIN basis_products bp ON p.basis_product_id = bp.id
        JOIN product_types pt ON p.product_type_id = pt.id
        JOIN directions d ON p.direction_id = d.id
        JOIN strike_currencies sc ON p.strike_currency_id = sc.id
        JOIN actions a ON t.action_id = a.id
        GROUP BY t.trade_id, p.id
        HAVING SUM(open_qty) > 0
        ORDER BY p.id;
        """).fetchall()
    ]


def update_open_qty(trade_id, open_qty):
    conn = get_db()
    conn.execute("UPDATE transactions SET open_qty = ? WHERE trade_id = ?", (open_qty, trade_id,))
    conn.commit()

def update_loss_carryforward(amount, user_id="default"):
    conn=get_db()
    conn.execute("UPDATE settings SET loss_carryforward = ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    st.session_state.loss_carryforward = amount

def update_tax_allowance(amount, user_id="default"):
    conn=get_db()
    conn.execute("UPDATE settings SET tax_allowance = ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    st.session_state.tax_allowance = amount
