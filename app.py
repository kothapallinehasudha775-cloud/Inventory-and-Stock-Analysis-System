import csv
import io
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, Response, g

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "local-dev-key-change-before-deployment")
DATABASE = os.path.join(app.root_path, "instance", "inventory.db")


def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            supplier TEXT NOT NULL DEFAULT '',
            cost_price REAL NOT NULL CHECK(cost_price >= 0),
            selling_price REAL NOT NULL CHECK(selling_price >= 0),
            quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
            reorder_level INTEGER NOT NULL DEFAULT 5 CHECK(reorder_level >= 0),
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL CHECK(transaction_type IN ('IN', 'OUT')),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE RESTRICT
        );
    """)
    db.commit()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_product_form():
    try:
        data = {
            "sku": request.form.get("sku", "").strip().upper(),
            "name": request.form.get("name", "").strip(),
            "category": request.form.get("category", "").strip(),
            "supplier": request.form.get("supplier", "").strip(),
            "cost_price": float(request.form.get("cost_price", "0")),
            "selling_price": float(request.form.get("selling_price", "0")),
            "quantity": int(request.form.get("quantity", "0")),
            "reorder_level": int(request.form.get("reorder_level", "5")),
        }
    except ValueError:
        raise ValueError("Enter valid numbers for prices, quantity, and reorder level.")
    if not data["sku"] or not data["name"] or not data["category"]:
        raise ValueError("SKU, product name, and category are required.")
    if data["cost_price"] < 0 or data["selling_price"] < 0:
        raise ValueError("Prices cannot be negative.")
    if data["quantity"] < 0 or data["reorder_level"] < 0:
        raise ValueError("Quantity and reorder level cannot be negative.")
    return data


@app.route("/")
def index():
    db = get_db()
    summary = db.execute("""
        SELECT COUNT(*) AS product_count,
               COALESCE(SUM(quantity), 0) AS units,
               COALESCE(SUM(quantity * cost_price), 0) AS inventory_cost,
               COALESCE(SUM(quantity * selling_price), 0) AS potential_sales,
               COALESCE(SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END), 0) AS out_count,
               COALESCE(SUM(CASE WHEN quantity > 0 AND quantity <= reorder_level THEN 1 ELSE 0 END), 0) AS low_count
        FROM products
    """).fetchone()
    low_stock = db.execute("""
        SELECT * FROM products WHERE quantity <= reorder_level
        ORDER BY quantity ASC, name ASC LIMIT 8
    """).fetchall()
    recent = db.execute("""
        SELECT t.*, p.name AS product_name, p.sku
        FROM transactions t JOIN products p ON p.id = t.product_id
        ORDER BY t.id DESC LIMIT 6
    """).fetchall()
    return render_template("index.html", summary=summary, low_stock=low_stock, recent=recent)


@app.route("/products")
def products():
    db = get_db()
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    if search:
        query += " AND (name LIKE ? OR sku LIKE ? OR supplier LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY name COLLATE NOCASE"
    rows = db.execute(query, params).fetchall()
    categories = db.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    return render_template("products.html", products=rows, categories=categories,
                           search=search, selected_category=category)


@app.route("/products/new", methods=["GET", "POST"])
def new_product():
    if request.method == "POST":
        try:
            data = read_product_form()
            db = get_db()
            db.execute("""INSERT INTO products
                (sku, name, category, supplier, cost_price, selling_price, quantity, reorder_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (data["sku"], data["name"], data["category"], data["supplier"],
                 data["cost_price"], data["selling_price"], data["quantity"],
                 data["reorder_level"], now()))
            db.commit()
            flash("Product added successfully.", "success")
            return redirect(url_for("products"))
        except ValueError as exc:
            flash(str(exc), "error")
        except sqlite3.IntegrityError:
            flash("That SKU already exists. Use a unique SKU.", "error")
    return render_template("product_form.html", product=None, page_title="Add product")


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("products"))
    if request.method == "POST":
        try:
            data = read_product_form()
            db.execute("""UPDATE products SET sku=?, name=?, category=?, supplier=?,
                cost_price=?, selling_price=?, quantity=?, reorder_level=? WHERE id=?""",
                (data["sku"], data["name"], data["category"], data["supplier"],
                 data["cost_price"], data["selling_price"], data["quantity"],
                 data["reorder_level"], product_id))
            db.commit()
            flash("Product updated successfully.", "success")
            return redirect(url_for("products"))
        except ValueError as exc:
            flash(str(exc), "error")
        except sqlite3.IntegrityError:
            flash("That SKU already belongs to another product.", "error")
    return render_template("product_form.html", product=product, page_title="Edit product")


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    db = get_db()
    try:
        db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        flash("Product deleted.", "success")
    except sqlite3.IntegrityError:
        db.rollback()
        flash("This product has stock history and cannot be deleted. Keep it for audit purposes.", "error")
    return redirect(url_for("products"))


@app.route("/transactions")
def transactions():
    rows = get_db().execute("""
        SELECT t.*, p.name AS product_name, p.sku
        FROM transactions t JOIN products p ON p.id = t.product_id
        ORDER BY t.id DESC LIMIT 200
    """).fetchall()
    return render_template("transactions.html", transactions=rows)


@app.route("/transactions/new", methods=["GET", "POST"])
def new_transaction():
    db = get_db()
    product_rows = db.execute("SELECT id, sku, name, quantity FROM products ORDER BY name").fetchall()
    if request.method == "POST":
        try:
            product_id = int(request.form.get("product_id", ""))
            quantity = int(request.form.get("quantity", "0"))
            kind = request.form.get("transaction_type", "")
            note = request.form.get("note", "").strip()
            product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if product is None:
                raise ValueError("Choose a valid product.")
            if kind not in ("IN", "OUT"):
                raise ValueError("Choose stock-in or stock-out.")
            if quantity <= 0:
                raise ValueError("Transaction quantity must be greater than zero.")
            if kind == "OUT" and quantity > product["quantity"]:
                raise ValueError(f"Only {product['quantity']} units are currently available.")
            new_quantity = product["quantity"] + quantity if kind == "IN" else product["quantity"] - quantity
            db.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_quantity, product_id))
            db.execute("""INSERT INTO transactions
                (product_id, transaction_type, quantity, note, created_at)
                VALUES (?, ?, ?, ?, ?)""", (product_id, kind, quantity, note, now()))
            db.commit()
            flash(f"Stock {('added' if kind == 'IN' else 'removed')} successfully.", "success")
            return redirect(url_for("transactions"))
        except (ValueError, TypeError) as exc:
            flash(str(exc) or "Enter valid transaction details.", "error")
    return render_template("transaction_form.html", products=product_rows)


@app.route("/export.csv")
def export_csv():
    rows = get_db().execute("""
        SELECT sku, name, category, supplier, cost_price, selling_price, quantity,
               reorder_level, quantity * cost_price AS inventory_cost
        FROM products ORDER BY name
    """).fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["SKU", "Product", "Category", "Supplier", "Cost Price",
                     "Selling Price", "Quantity", "Reorder Level", "Inventory Cost"])
    for row in rows:
        writer.writerow(list(row))
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=inventory.csv"})


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)
