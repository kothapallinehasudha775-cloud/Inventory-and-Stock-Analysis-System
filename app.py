import os
from datetime import date
from decimal import Decimal

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from flask import Flask, flash, redirect, render_template, request, url_for
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-development-secret")


def get_connection():
    """Create a MySQL connection using environment variables."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "inventory_db"),
    )


def query_all(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def get_dashboard_data():
    products = query_all("""
        SELECT p.product_id, p.sku, p.product_name, p.category,
               p.reorder_level, p.unit_cost,
               COALESCE(SUM(CASE
                   WHEN st.transaction_type = 'IN' THEN st.quantity
                   WHEN st.transaction_type = 'OUT' THEN -st.quantity
                   WHEN st.transaction_type = 'ADJUSTMENT' THEN st.quantity
                   ELSE 0 END), 0) + p.opening_stock AS current_stock
        FROM products p
        LEFT JOIN stock_transactions st ON st.product_id = p.product_id
        GROUP BY p.product_id, p.sku, p.product_name, p.category,
                 p.reorder_level, p.unit_cost, p.opening_stock
        ORDER BY p.product_name
    """)
    df = pd.DataFrame(products)
    if df.empty:
        low_stock = []
        total_products = 0
        total_units = 0
        inventory_value = 0.0
        movement = []
    else:
        df["current_stock"] = pd.to_numeric(df["current_stock"])
        df["unit_cost"] = pd.to_numeric(df["unit_cost"])
        df["inventory_value"] = np.maximum(df["current_stock"], 0) * df["unit_cost"]
        low_stock = df[df["current_stock"] <= df["reorder_level"]].to_dict("records")
        total_products = len(df)
        total_units = int(df["current_stock"].sum())
        inventory_value = float(df["inventory_value"].sum())
        movement = query_all("""
            SELECT p.product_name,
                   COALESCE(SUM(CASE WHEN st.transaction_type='IN' THEN st.quantity ELSE 0 END),0) AS stock_in,
                   COALESCE(SUM(CASE WHEN st.transaction_type='OUT' THEN st.quantity ELSE 0 END),0) AS stock_out
            FROM products p
            LEFT JOIN stock_transactions st ON st.product_id=p.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY (stock_in + stock_out) DESC, p.product_name
            LIMIT 10
        """)
    return products, low_stock, total_products, total_units, inventory_value, movement


def create_movement_chart(movement):
    os.makedirs(os.path.join(app.static_folder, "charts"), exist_ok=True)
    path = os.path.join(app.static_folder, "charts", "movement.png")
    if not movement:
        plt.figure(figsize=(8, 3))
        plt.text(0.5, 0.5, "No stock movement data yet", ha="center", va="center")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        return "charts/movement.png"
    df = pd.DataFrame(movement)
    x = np.arange(len(df))
    width = 0.38
    plt.figure(figsize=(10, 4.5))
    plt.bar(x - width / 2, df["stock_in"], width, label="Stock in")
    plt.bar(x + width / 2, df["stock_out"], width, label="Stock out")
    plt.xticks(x, df["product_name"], rotation=35, ha="right")
    plt.ylabel("Units")
    plt.title("Product Stock Movement (Top 10)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()
    return "charts/movement.png"


@app.route("/")
def dashboard():
    try:
        products, low_stock, total_products, total_units, inventory_value, movement = get_dashboard_data()
        chart = create_movement_chart(movement)
        return render_template("dashboard.html", products=products, low_stock=low_stock,
                               total_products=total_products, total_units=total_units,
                               inventory_value=inventory_value, chart=chart)
    except Error as exc:
        return render_template("error.html", message=f"Could not connect to MySQL: {exc}")


@app.route("/products", methods=["GET", "POST"])
def products_page():
    if request.method == "POST":
        try:
            sku = request.form["sku"].strip()
            name = request.form["product_name"].strip()
            category = request.form.get("category", "").strip()
            reorder = int(request.form["reorder_level"])
            cost = Decimal(request.form["unit_cost"])
            opening = int(request.form.get("opening_stock", "0"))
            if not sku or not name or reorder < 0 or cost < 0 or opening < 0:
                raise ValueError("Please provide valid values. Stock, reorder level, and cost cannot be negative.")
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""INSERT INTO products
                (sku, product_name, category, reorder_level, unit_cost, opening_stock)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (sku, name, category or None, reorder, cost, opening))
            conn.commit()
            flash("Product added successfully.", "success")
            return redirect(url_for("products_page"))
        except (ValueError, Error) as exc:
            flash(f"Could not add product: {exc}", "danger")
        finally:
            if "cur" in locals():
                cur.close()
            if "conn" in locals() and conn.is_connected():
                conn.close()
    try:
        products = query_all("""
            SELECT p.*,
              p.opening_stock + COALESCE(SUM(CASE
                WHEN st.transaction_type='IN' THEN st.quantity
                WHEN st.transaction_type='OUT' THEN -st.quantity
                WHEN st.transaction_type='ADJUSTMENT' THEN st.quantity
                ELSE 0 END),0) AS current_stock
            FROM products p LEFT JOIN stock_transactions st ON p.product_id=st.product_id
            GROUP BY p.product_id ORDER BY p.product_name
        """)
        suppliers = query_all("SELECT * FROM suppliers ORDER BY supplier_name")
        return render_template("products.html", products=products, suppliers=suppliers)
    except Error as exc:
        return render_template("error.html", message=f"Database error: {exc}")


@app.route("/suppliers", methods=["GET", "POST"])
def suppliers_page():
    if request.method == "POST":
        try:
            name = request.form["supplier_name"].strip()
            contact = request.form.get("contact_name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            if not name:
                raise ValueError("Supplier name is required.")
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""INSERT INTO suppliers (supplier_name, contact_name, email, phone)
                           VALUES (%s,%s,%s,%s)""",
                        (name, contact or None, email or None, phone or None))
            conn.commit()
            flash("Supplier added successfully.", "success")
            return redirect(url_for("suppliers_page"))
        except (ValueError, Error) as exc:
            flash(f"Could not add supplier: {exc}", "danger")
        finally:
            if "cur" in locals():
                cur.close()
            if "conn" in locals() and conn.is_connected():
                conn.close()
    try:
        suppliers = query_all("SELECT * FROM suppliers ORDER BY supplier_name")
        return render_template("suppliers.html", suppliers=suppliers)
    except Error as exc:
        return render_template("error.html", message=f"Database error: {exc}")


@app.route("/transactions", methods=["GET", "POST"])
def transactions_page():
    if request.method == "POST":
        conn = None
        cur = None
        try:
            product_id = int(request.form["product_id"])
            transaction_type = request.form["transaction_type"]
            quantity = int(request.form["quantity"])
            transaction_date = request.form.get("transaction_date") or date.today().isoformat()
            supplier_value = request.form.get("supplier_id", "").strip()
            supplier_id = int(supplier_value) if supplier_value else None
            note = request.form.get("note", "").strip() or None
            if transaction_type not in ("IN", "OUT", "ADJUSTMENT"):
                raise ValueError("Invalid transaction type.")
            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero.")
            if transaction_type == "ADJUSTMENT":
                raise ValueError("Use the adjustment form below with a signed quantity for stock corrections.")

            conn = get_connection()
            conn.start_transaction()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT product_id, opening_stock FROM products WHERE product_id=%s FOR UPDATE",
                        (product_id,))
            product = cur.fetchone()
            if not product:
                raise ValueError("Product not found.")
            cur.execute("""SELECT COALESCE(SUM(CASE
                WHEN transaction_type='IN' THEN quantity
                WHEN transaction_type='OUT' THEN -quantity
                WHEN transaction_type='ADJUSTMENT' THEN quantity
                ELSE 0 END),0) AS net
                FROM stock_transactions WHERE product_id=%s""", (product_id,))
            current_stock = int(product["opening_stock"]) + int(cur.fetchone()["net"])
            if transaction_type == "OUT" and quantity > current_stock:
                raise ValueError(f"Insufficient stock. Current stock is {current_stock}; stock cannot become negative.")
            cur.execute("""INSERT INTO stock_transactions
                (product_id, transaction_date, transaction_type, quantity, supplier_id, note)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (product_id, transaction_date, transaction_type, quantity, supplier_id, note))
            conn.commit()
            flash("Stock transaction recorded.", "success")
            return redirect(url_for("transactions_page"))
        except (ValueError, Error) as exc:
            if conn and conn.is_connected():
                conn.rollback()
            flash(f"Transaction not saved: {exc}", "danger")
        finally:
            if cur:
                cur.close()
            if conn and conn.is_connected():
                conn.close()

    try:
        products = query_all("SELECT product_id, sku, product_name FROM products ORDER BY product_name")
        suppliers = query_all("SELECT supplier_id, supplier_name FROM suppliers ORDER BY supplier_name")
        transactions = query_all("""
            SELECT st.*, p.sku, p.product_name, s.supplier_name
            FROM stock_transactions st
            JOIN products p ON p.product_id=st.product_id
            LEFT JOIN suppliers s ON s.supplier_id=st.supplier_id
            ORDER BY st.transaction_date DESC, st.transaction_id DESC LIMIT 200
        """)
        return render_template("transactions.html", products=products, suppliers=suppliers,
                               transactions=transactions, today=date.today().isoformat())
    except Error as exc:
        return render_template("error.html", message=f"Database error: {exc}")


@app.route("/reports")
def reports_page():
    try:
        products, low_stock, total_products, total_units, inventory_value, movement = get_dashboard_data()
        history = query_all("""
            SELECT DATE_FORMAT(transaction_date, '%Y-%m') AS month,
                   SUM(CASE WHEN transaction_type='IN' THEN quantity ELSE 0 END) AS stock_in,
                   SUM(CASE WHEN transaction_type='OUT' THEN quantity ELSE 0 END) AS stock_out
            FROM stock_transactions
            GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
            ORDER BY month
        """)
        history_df = pd.DataFrame(history)
        if not history_df.empty:
            history_df["net_movement"] = history_df["stock_in"] - history_df["stock_out"]
            history = history_df.to_dict("records")
        return render_template("reports.html", products=products, low_stock=low_stock,
                               inventory_value=inventory_value, history=history)
    except Error as exc:
        return render_template("error.html", message=f"Database error: {exc}")


if __name__ == "__main__":
    app.run(debug=True)
