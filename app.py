"""StockWise - Inventory and Stock Analysis System (Flask + MySQL + Pandas/NumPy/Matplotlib)."""
import io
import os
from contextlib import closing
from datetime import date

import matplotlib
matplotlib.use("Agg")  # no display needed on a server
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymysql
from flask import (Flask, Response, flash, redirect, render_template,
                   request, url_for)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

IN_TYPES = ("IN", "ADJUST_IN")
OUT_TYPES = ("OUT", "ADJUST_OUT")
TYPE_LABELS = {"IN": "Stock in", "OUT": "Stock out",
               "ADJUST_IN": "Adjustment (add)", "ADJUST_OUT": "Adjustment (remove)"}
NET = ("CASE WHEN t.transaction_type IN ('IN','ADJUST_IN') THEN t.quantity "
       "WHEN t.transaction_type IN ('OUT','ADJUST_OUT') THEN -t.quantity ELSE 0 END")


# ---------------------------------------------------------------- database
def get_conn():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "inventory_db"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def q(sql, args=None):
    """Run a SELECT and return a list of dict rows."""
    with closing(get_conn()) as c, c.cursor() as cur:
        cur.execute(sql, args or ())
        return list(cur.fetchall())


def run(sql, args=None):
    with closing(get_conn()) as c:
        with c.cursor() as cur:
            cur.execute(sql, args or ())
        c.commit()


# ---------------------------------------------------------------- analysis
STOCK_COLS = ["product_id", "sku", "product_name", "category", "opening_balance",
              "reorder_level", "unit_cost", "current_stock"]


def stock_df():
    """Current stock = opening balance + all transactions (calculated, never typed in)."""
    rows = q(f"""SELECT p.product_id, p.sku, p.product_name, p.category, p.opening_balance,
                        p.reorder_level, p.unit_cost,
                        p.opening_balance + COALESCE(SUM({NET}), 0) AS current_stock
                 FROM products p LEFT JOIN stock_transactions t ON t.product_id = p.product_id
                 GROUP BY p.product_id, p.sku, p.product_name, p.category,
                          p.opening_balance, p.reorder_level, p.unit_cost
                 ORDER BY p.product_name""")
    df = pd.DataFrame(rows, columns=STOCK_COLS)
    df["current_stock"] = df["current_stock"].astype(int)
    df["unit_cost"] = df["unit_cost"].astype(float)
    s = df["current_stock"].to_numpy()
    rl = df["reorder_level"].to_numpy()
    df["stock_value"] = np.round(s * df["unit_cost"].to_numpy(), 2)
    df["low"] = s < rl
    df["status"] = np.where(s == 0, "Out of stock", np.where(s < rl, "Low", "OK"))
    df["suggested_order"] = np.where(s < rl, np.maximum(rl * 2 - s, 0), 0)
    return df


def txn_df():
    rows = q("""SELECT t.transaction_id, t.transaction_date, t.transaction_type, t.quantity,
                       t.note, t.product_id, p.sku, p.product_name,
                       COALESCE(s.supplier_name, '') AS supplier_name
                FROM stock_transactions t
                JOIN products p ON p.product_id = t.product_id
                LEFT JOIN suppliers s ON s.supplier_id = t.supplier_id
                ORDER BY t.transaction_date, t.transaction_id""")
    cols = ["transaction_id", "transaction_date", "transaction_type", "quantity", "note",
            "product_id", "sku", "product_name", "supplier_name"]
    df = pd.DataFrame(rows, columns=cols)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["quantity"] = df["quantity"].astype(int)
    df["signed_qty"] = np.where(df["transaction_type"].isin(IN_TYPES), df["quantity"], -df["quantity"])
    return df


def movement_summary(sdf, tdf):
    """Fast-moving products: units sent out in the last 30 days of recorded activity."""
    if tdf.empty:
        return pd.DataFrame(columns=["sku", "product_name", "units_out", "share_pct", "days_left"])
    end = tdf["transaction_date"].max()
    recent = tdf[(tdf["transaction_type"] == "OUT") &
                 (tdf["transaction_date"] > end - pd.Timedelta(days=30))]
    out = recent.groupby("product_id")["quantity"].sum().rename("units_out").reset_index()
    m = sdf.merge(out, on="product_id", how="left").fillna({"units_out": 0})
    m["units_out"] = m["units_out"].astype(int)
    total = max(int(m["units_out"].sum()), 1)
    m["share_pct"] = np.round(m["units_out"].to_numpy() / total * 100, 1)
    rate = m["units_out"].to_numpy() / 30.0
    with np.errstate(divide="ignore", invalid="ignore"):
        m["days_left"] = np.where(rate > 0, np.round(m["current_stock"].to_numpy() / rate, 0), np.nan)
    return m.sort_values("units_out", ascending=False)[
        ["sku", "product_name", "units_out", "share_pct", "current_stock", "days_left"]]


def reconcile(sdf, tdf):
    """Rebuild every balance from raw history with a running total and compare to the SQL figure."""
    rows = []
    for _, p in sdf.iterrows():
        h = tdf[tdf["product_id"] == p["product_id"]]
        running = p["opening_balance"] + h["signed_qty"].cumsum()
        rebuilt = int(p["opening_balance"] + h["signed_qty"].sum())
        lowest = int(running.min()) if len(h) else int(p["opening_balance"])
        ok = rebuilt == int(p["current_stock"]) and lowest >= 0
        rows.append({"sku": p["sku"], "product_name": p["product_name"],
                     "opening": int(p["opening_balance"]),
                     "in_qty": int(h.loc[h["signed_qty"] > 0, "signed_qty"].sum()),
                     "out_qty": int(-h.loc[h["signed_qty"] < 0, "signed_qty"].sum()),
                     "rebuilt": rebuilt, "reported": int(p["current_stock"]),
                     "lowest": lowest, "ok": ok})
    return rows


# ---------------------------------------------------------------- stock rules
def add_transaction(product_id, ttype, qty, tdate, supplier_id, note):
    """Insert a movement. Refuses anything that would make stock negative."""
    if ttype not in TYPE_LABELS:
        raise ValueError("Choose a valid movement type.")
    if qty <= 0:
        raise ValueError("Quantity must be a positive whole number.")
    if ttype.startswith("ADJUST") and not note.strip():
        raise ValueError("Adjustments need a reason in the note so they can be audited.")
    with closing(get_conn()) as c:
        try:
            with c.cursor() as cur:
                cur.execute("SELECT opening_balance FROM products WHERE product_id=%s FOR UPDATE",
                            (product_id,))
                p = cur.fetchone()
                if not p:
                    raise ValueError("Product not found.")
                cur.execute(f"SELECT COALESCE(SUM({NET}), 0) AS net FROM stock_transactions t "
                            "WHERE t.product_id=%s", (product_id,))
                stock = int(p["opening_balance"]) + int(cur.fetchone()["net"])
                if ttype in OUT_TYPES and qty > stock:
                    raise ValueError(f"Not enough stock. Available: {stock}, requested: {qty}.")
                cur.execute("""INSERT INTO stock_transactions
                    (product_id, transaction_date, transaction_type, quantity, supplier_id, note)
                    VALUES (%s,%s,%s,%s,%s,%s)""",
                    (product_id, tdate, ttype, qty, supplier_id, note.strip() or None))
            c.commit()
        except Exception:
            c.rollback()
            raise


# ---------------------------------------------------------------- pages
@app.route("/")
def dashboard():
    sdf = stock_df()
    low = sdf[sdf["low"]]
    return render_template("dashboard.html", n_products=len(sdf),
                           units=int(sdf["current_stock"].sum()),
                           value=float(sdf["stock_value"].sum()), low=low.to_dict("records"))


@app.route("/products", methods=["GET", "POST"])
def products():
    if request.method == "POST":
        f = request.form
        try:
            run("""INSERT INTO products (sku, product_name, category, opening_balance,
                   reorder_level, unit_cost) VALUES (%s,%s,%s,%s,%s,%s)""",
                (f["sku"].strip(), f["product_name"].strip(), f["category"].strip(),
                 max(int(f["opening_balance"]), 0), max(int(f["reorder_level"]), 0),
                 max(float(f["unit_cost"]), 0)))
            flash("Product added.", "ok")
        except pymysql.err.IntegrityError:
            flash("That SKU already exists. Use a different SKU.", "err")
        except (ValueError, KeyError):
            flash("Check the numbers: stock, reorder level and cost must be valid.", "err")
        return redirect(url_for("products"))
    return render_template("products.html", rows=stock_df().to_dict("records"))


@app.route("/products/<int:pid>/settings", methods=["POST"])
def product_settings(pid):
    try:
        run("UPDATE products SET reorder_level=%s, unit_cost=%s WHERE product_id=%s",
            (max(int(request.form["reorder_level"]), 0),
             max(float(request.form["unit_cost"]), 0), pid))
        flash("Reorder level and cost updated.", "ok")
    except (ValueError, KeyError):
        flash("Enter valid numbers.", "err")
    return redirect(url_for("products"))


@app.route("/suppliers", methods=["GET", "POST"])
def suppliers():
    if request.method == "POST":
        name = request.form.get("supplier_name", "").strip()
        if not name:
            flash("Supplier name is required.", "err")
        else:
            try:
                run("INSERT INTO suppliers (supplier_name, contact_email) VALUES (%s,%s)",
                    (name, request.form.get("contact_email", "").strip() or None))
                flash("Supplier added.", "ok")
            except pymysql.err.IntegrityError:
                flash("That supplier already exists.", "err")
        return redirect(url_for("suppliers"))
    return render_template("suppliers.html", rows=q("SELECT * FROM suppliers ORDER BY supplier_name"))


@app.route("/transactions", methods=["GET", "POST"])
def transactions():
    if request.method == "POST":
        f = request.form
        try:
            add_transaction(int(f["product_id"]), f["transaction_type"], int(f["quantity"]),
                            f["transaction_date"] or date.today().isoformat(),
                            int(f["supplier_id"]) if f.get("supplier_id") else None,
                            f.get("note", ""))
            flash("Movement recorded.", "ok")
        except ValueError as e:
            flash(str(e), "err")
        except (KeyError, pymysql.MySQLError):
            flash("Could not save the movement. Check the form and try again.", "err")
        return redirect(url_for("transactions"))
    pid = request.args.get("product_id", type=int)
    tdf = txn_df().sort_values(["transaction_date", "transaction_id"], ascending=False)
    if pid:
        tdf = tdf[tdf["product_id"] == pid]
    tdf = tdf.assign(transaction_date=tdf["transaction_date"].dt.strftime("%Y-%m-%d"))
    return render_template("transactions.html", rows=tdf.head(200).to_dict("records"),
                           products=q("SELECT product_id, sku, product_name FROM products ORDER BY product_name"),
                           suppliers=q("SELECT supplier_id, supplier_name FROM suppliers ORDER BY supplier_name"),
                           labels=TYPE_LABELS, today=date.today().isoformat(), selected=pid)


@app.route("/reports")
def reports():
    sdf, tdf = stock_df(), txn_df()
    cat = sdf.groupby("category").agg(units=("current_stock", "sum"),
                                      value=("stock_value", "sum")).reset_index()
    mv = movement_summary(sdf, tdf)
    mv = mv.assign(days_left=mv["days_left"].map(lambda x: "-" if pd.isna(x) else int(x)))
    return render_template("reports.html", stock=sdf.to_dict("records"),
                           low=sdf[sdf["low"]].to_dict("records"),
                           cats=cat.to_dict("records"), moves=mv.head(5).to_dict("records"),
                           rec=reconcile(sdf, tdf), total=float(sdf["stock_value"].sum()))


# ---------------------------------------------------------------- charts and exports
def png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    return Response(buf.getvalue(), mimetype="image/png")


@app.route("/chart/stock.png")
def chart_stock():
    sdf = stock_df().sort_values("current_stock")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    colors = np.where(sdf["low"], "#B42318", "#1F6F5C")
    ax.barh(sdf["product_name"], sdf["current_stock"], color=colors)
    ax.scatter(sdf["reorder_level"], sdf["product_name"], marker="|", s=320,
               color="#1B2430", zorder=3, label="Reorder level")
    ax.set_xlabel("Units in stock")
    ax.set_title("Stock level vs reorder level (red = below reorder level)", fontsize=10, loc="left")
    ax.legend(loc="lower right", frameon=False)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    return png(fig)


@app.route("/chart/movement.png")
def chart_movement():
    tdf = txn_df()
    fig, ax = plt.subplots(figsize=(8, 4.2))
    if tdf.empty:
        ax.text(0.5, 0.5, "No movements yet", ha="center")
    else:
        tdf["month"] = tdf["transaction_date"].dt.to_period("M").astype(str)
        tdf["dir"] = np.where(tdf["signed_qty"] > 0, "In", "Out")
        pv = tdf.pivot_table(index="month", columns="dir", values="quantity",
                             aggfunc="sum", fill_value=0).reindex(columns=["In", "Out"], fill_value=0)
        x = np.arange(len(pv))
        ax.bar(x - 0.2, pv["In"], 0.4, label="Stock in", color="#1F6F5C")
        ax.bar(x + 0.2, pv["Out"], 0.4, label="Stock out", color="#C2410C")
        ax.set_xticks(x)
        ax.set_xticklabels(pv.index)
        ax.set_ylabel("Units")
        ax.legend(frameon=False)
    ax.set_title("Monthly stock movement", fontsize=10, loc="left")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    return png(fig)


def csv_response(df, name):
    return Response(df.to_csv(index=False), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={name}"})


@app.route("/export/stock.csv")
def export_stock():
    return csv_response(stock_df().drop(columns=["product_id", "low"]), "current_stock.csv")


@app.route("/export/low-stock.csv")
def export_low():
    d = stock_df()
    d = d[d["low"]][["sku", "product_name", "current_stock", "reorder_level", "suggested_order"]]
    return csv_response(d, "low_stock.csv")


@app.route("/export/transactions.csv")
def export_txn():
    return csv_response(txn_df().drop(columns=["signed_qty"]), "transactions.csv")


@app.template_filter("money")
def money(v):
    return f"\u20b9{v:,.2f}"


if __name__ == "__main__":
    app.run(debug=True)
