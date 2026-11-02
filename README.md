# Inventory and Stock Analysis System

A beginner-friendly Python + Flask + MySQL web application to manage products, suppliers, stock-in/stock-out transactions, low-stock alerts, inventory valuation, and movement reports.

## Features
- Add and list products and suppliers.
- Record stock-in and stock-out transactions with date, supplier, and notes.
- Calculate current stock from opening stock plus logged transactions.
- Block stock-out transactions that would make stock negative.
- Show products at or below their reorder level.
- Use Pandas and NumPy for stock and valuation analysis.
- Generate a Matplotlib product-movement chart.
- Keep a transaction history for audit/reconciliation.

## Technology
Python, Flask, MySQL, mysql-connector-python, Pandas, NumPy, Matplotlib, HTML/CSS (Bootstrap CDN).

## 1. Requirements
- Python 3.10 or newer
- MySQL Server 8.x (or compatible)
- Git
- A terminal / command prompt

## 2. Create the database
1. Start MySQL Server.
2. Open MySQL Workbench or a terminal connected to MySQL.
3. Run the complete `schema.sql` file. It creates `inventory_db`, tables, and optional sample data.
4. If you do not want sample data, remove the final two `INSERT` sections from `schema.sql` before running it.

Terminal example:
```bash
mysql -u root -p < schema.sql
```

## 3. Set up Python
From the project folder:

### Windows PowerShell
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Windows Command Prompt
```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and enter your actual MySQL username/password. Do not commit `.env` to Git.

Note: This starter app reads database settings from environment variables. If you use a `.env` file, add these two lines near the top of `app.py` after the imports:
```python
from dotenv import load_dotenv
load_dotenv()
```
(Alternatively, set the variables in your terminal before starting the app.)

## 4. Run the app
Activate the virtual environment, then:
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your browser.

## 5. Recommended first-use flow
1. Open **Suppliers** and add a supplier.
2. Open **Products** and add products with SKU, unit cost, reorder level, and opening stock.
3. Open **Transactions** and record stock-in or stock-out.
4. Open **Reports** to review low-stock items, estimated stock value, and monthly movement.
5. Return to **Dashboard** for a summary and movement chart.

## 6. GitHub: push your project
Create an empty repository on GitHub (do not initialize it with a README if you already have one locally). Then, from this project folder:

```bash
git init
git add .
git commit -m "Initial commit: inventory stock analysis system"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Replace the URL with your repository's actual URL. If Git says `remote origin already exists`, run:
```bash
git remote set-url origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Check the repository page after pushing. Never upload `.env`, passwords, or real business data.

## Stock calculation
`current_stock = opening_stock + total_stock_in - total_stock_out + signed_adjustments`

Regular transactions only accept positive quantities. Stock-out is rejected if the available quantity is too low. Any future adjustment workflow should require a reason and record a signed adjustment; this starter schema supports adjustments for audit purposes, while the current UI intentionally prevents unreviewed adjustments.

## Important production notes
- This is an educational project, not a hardened production inventory platform.
- `debug=True` is for local development only. Disable it before deployment.
- For multi-user production use, add authentication/authorization, CSRF protection, migrations, automated tests, and stricter transaction-level concurrency controls.
