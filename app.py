import os
import io
import csv
import base64
from datetime import datetime
from decimal import Decimal

import mysql.connector
from mysql.connector import Error
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-before-deploying")

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "inventory_db"),
    )

def query_inventory():
    sql = """
    SELECT p.product_id, p.sku, p.product_name, p.category,
           p.opening_stock, p.reorder_level, p.unit_cost,
           COALESCE(SUM(CASE WHEN t.transaction_type='IN' THEN t.quantity
                             WHEN t.transaction_type='OUT' THEN -t.quantity
                             ELSE 0 END), 0) AS movement,
           p.opening_stock + COALESCE(SUM(
               CASE WHEN t.transaction_type='IN' THEN t.quantity
                    WHEN t.transaction_type='OUT' THEN -t.quantity
                    ELSE 0 END), 0) AS current_stock
    FROM products p
    LEFT JOIN stock_transactions t ON p.product_id=t.product_id
    GROUP BY p.product_id, p.sku, p.product_name, p.category,
             p.opening_stock, p.reorder_level, p.unit_cost
    ORDER BY p.product_name
    """
    con = get_connection()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute(sql)
        return cur.fetchall()
    finally:
        con.close()

@app.route("/")
def dashboard():
    try:
        products = query_inventory()
        low_stock = [p for p in products if p["current_stock"] <= p["reorder_level"]]
        total_units = sum(int(p["current_stock"]) for p in products)
        total_value = sum(Decimal(str(p["current_stock"])) * Decimal(str(p["unit_cost"])) for p in products)
        return render_template("dashboard.html", products=products[:6], product_count=len(products),
                               total_units=total_units, total_value=total_value, low_stock=low_stock[:6],
                               low_count=len(low_stock))
    except Error as e:
        return render_template("setup_error.html", error=str(e))

@app.route("/products")
def products_page():
    try:
        return render_template("products.html", products=query_inventory())
    except Error as e:
        flash(f"Database error: {e}", "error")
        return render_template("products.html", products=[])

@app.route("/products/add", methods=["POST"])
def add_product():
    try:
        sku = request.form["sku"].strip()
        name = request.form["product_name"].strip()
        category = request.form.get("category", "").strip()
        opening = int(request.form["opening_stock"])
        reorder = int(request.form["reorder_level"])
        cost = float(request.form["unit_cost"])
        if not sku or not name or opening < 0 or reorder < 0 or cost < 0:
            raise ValueError("Enter a SKU and product name; numeric values must be non-negative.")
        con = get_connection()
        try:
            cur = con.cursor()
            cur.execute("""INSERT INTO products
                (sku, product_name, category, opening_stock, reorder_level, unit_cost)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (sku, name, category or None, opening, reorder, cost))
            con.commit()
        finally:
            con.close()
        flash("Product added successfully.", "success")
    except (ValueError, KeyError) as e:
        flash(str(e) or "Please enter valid values.", "error")
    except Error as e:
        flash(f"Could not add product. Check the SKU is unique and database is available. {e}", "error")
    return redirect(url_for("products_page"))

@app.route("/suppliers", methods=["GET", "POST"])
def suppliers_page():
    con = get_connection()
    try:
        cur = con.cursor(dictionary=True)
        if request.method == "POST":
            name = request.form.get("supplier_name", "").strip()
            phone = request.form.get("phone", "").strip()
            if not name:
                flash("Supplier name is required.", "error")
            else:
                cur.execute("INSERT INTO suppliers (supplier_name, phone) VALUES (%s,%s)",
                            (name, phone or None))
                con.commit()
                flash("Supplier added successfully.", "success")
                return redirect(url_for("suppliers_page"))
        cur.execute("SELECT supplier_id, supplier_name, phone FROM suppliers ORDER BY supplier_name")
        suppliers = cur.fetchall()
        return render_template("suppliers.html", suppliers=suppliers)
    finally:
        con.close()

@app.route("/transactions", methods=["GET", "POST"])
def transactions_page():
    if request.method == "POST":
        try:
            product_id = int(request.form["product_id"])
            quantity = int(request.form["quantity"])
            kind = request.form["transaction_type"].upper()
            supplier_raw = request.form.get("supplier_id", "").strip()
            supplier_id = int(supplier_raw) if supplier_raw else None
            if quantity <= 0 or kind not in ("IN", "OUT"):
                raise ValueError("Quantity must be positive and type must be IN or OUT.")
            con = get_connection()
            try:
                cur = con.cursor()
                cur.execute("""
                    SELECT p.opening_stock + COALESCE(SUM(
                      CASE WHEN t.transaction_type='IN' THEN t.quantity
                           WHEN t.transaction_type='OUT' THEN -t.quantity ELSE 0 END),0)
                    FROM products p LEFT JOIN stock_transactions t ON p.product_id=t.product_id
                    WHERE p.product_id=%s GROUP BY p.product_id,p.opening_stock
                """, (product_id,))
                row = cur.fetchone()
                if row is None:
                    raise ValueError("Product not found.")
                if kind == "OUT" and quantity > int(row[0]):
                    raise ValueError(f"Insufficient stock. Available quantity: {row[0]}")
                cur.execute("""INSERT INTO stock_transactions
                    (product_id, transaction_type, quantity, supplier_id)
                    VALUES (%s,%s,%s,%s)""", (product_id, kind, quantity, supplier_id if kind == "IN" else None))
                con.commit()
            finally:
                con.close()
            flash("Stock transaction recorded.", "success")
            return redirect(url_for("transactions_page"))
        except (ValueError, KeyError) as e:
            flash(str(e) or "Please check the form values.", "error")
        except Error as e:
            flash(f"Database error: {e}", "error")
    con = get_connection()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT product_id, product_name FROM products ORDER BY product_name")
        products = cur.fetchall()
        cur.execute("""SELECT t.transaction_id, t.transaction_date, t.transaction_type,
                              t.quantity, p.product_name, s.supplier_name
                       FROM stock_transactions t
                       JOIN products p ON p.product_id=t.product_id
                       LEFT JOIN suppliers s ON s.supplier_id=t.supplier_id
                       ORDER BY t.transaction_date DESC, t.transaction_id DESC LIMIT 100""")
        transactions = cur.fetchall()
        cur.execute("SELECT supplier_id, supplier_name FROM suppliers ORDER BY supplier_name")
        suppliers = cur.fetchall()
        return render_template("transactions.html", products=products, transactions=transactions, suppliers=suppliers)
    finally:
        con.close()

@app.route("/analytics")
def analytics():
    try:
        products = query_inventory()
        if not products:
            return render_template("analytics.html", products=[], total_value=0, low_stock=[], chart=None)
        df = pd.DataFrame(products)
        df["current_stock"] = pd.to_numeric(df["current_stock"])
        df["unit_cost"] = pd.to_numeric(df["unit_cost"])
        df["stock_value"] = np.multiply(df["current_stock"].to_numpy(), df["unit_cost"].to_numpy())
        low_stock = df[df["current_stock"] <= pd.to_numeric(df["reorder_level"])]
        chart_buf = io.BytesIO()
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.bar(df["product_name"], df["current_stock"])
        ax.set_title("Current Stock by Product")
        ax.set_xlabel("Product")
        ax.set_ylabel("Units")
        ax.tick_params(axis="x", labelrotation=30)
        fig.tight_layout()
        fig.savefig(chart_buf, format="png", dpi=130)
        plt.close(fig)
        chart_buf.seek(0)
        return render_template("analytics.html", products=df.to_dict("records"),
                               total_value=float(df["stock_value"].sum()),
                               low_stock=low_stock.to_dict("records"),
                               chart=base64.b64encode(chart_buf.getvalue()).decode("ascii"))
    except Error as e:
        flash(f"Database error: {e}", "error")
        return render_template("analytics.html", products=[], total_value=0, low_stock=[], chart=None)

@app.route("/report.csv")
def report_csv():
    try:
        products = query_inventory()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["SKU", "Product", "Category", "Current Stock", "Reorder Level", "Unit Cost", "Stock Value"])
        for p in products:
            writer.writerow([p["sku"], p["product_name"], p["category"], p["current_stock"],
                             p["reorder_level"], p["unit_cost"],
                             float(p["current_stock"]) * float(p["unit_cost"])])
        return Response(output.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=inventory_report.csv"})
    except Error as e:
        flash(f"Could not create report: {e}", "error")
        return redirect(url_for("analytics"))

if __name__ == "__main__":
    app.run(debug=True)
