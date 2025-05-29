import os
import sqlite3

def get_db():
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, "..", "db", "test.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


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
        (row["trade_id"], f"{row['direction']} @ {row['strike']}{row['currency']} {row['basis_name']}"
                          f" (Open Quantity: {row['open_qty']})", row["open_qty"], row["product_id"], row["price_paid"])
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
