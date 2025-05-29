from utils.db_helper import get_db

def get_new_trade_id():
    conn = get_db()
    result = conn.execute("SELECT MAX(trade_id) FROM transactions").fetchone()
    return result[0]+1 if result[0] is not None else 0


def get_or_create_trade_id(product_id):
    conn = get_db()
    result = conn.execute("""
        SELECT trade_id
        FROM transactions
        WHERE product_id = ? AND open_qty > 0
        ORDER BY date ASC
        LIMIT 1
    """, (product_id,)).fetchone()

    if result:
        return result[0]
    else:
        result = conn.execute("SELECT MAX(trade_id) FROM transactions").fetchone()
        return (result[0] + 1) if result[0] is not None else 0


def get_direction_id(direction):
    conn = get_db()
    return conn.execute("SELECT id FROM directions WHERE name LIKE ?", (direction,)).fetchone()[0]


def get_or_create_product_id(basis_id, product_type_id, direction_id, strike, strike_currency_id, wkn, name, expiry_date):
    conn = get_db()
    exists= conn.execute("SELECT id FROM products WHERE "
                   "basis_product_id = ? AND "
                   "product_type_id = ? AND "
                   "direction_id = ? AND "
                   "strike = ? AND "
                   "strike_currency_id = ?",
                   (basis_id,product_type_id,direction_id,strike,strike_currency_id)).fetchone()
    if exists:
        return exists[0]
    else:
        conn.execute("INSERT INTO products (basis_product_id,product_type_id,direction_id,"
                       "strike,strike_currency_id,wkn,name,expiry_date) "
                       "VALUES (?,?,?,?,?,?,?,?)",
                       (basis_id, product_type_id, direction_id, strike, strike_currency_id,
                        wkn, name, expiry_date,))
        conn.commit()
        return conn.execute("SELECT MAX(id) FROM products").fetchone()[0]
