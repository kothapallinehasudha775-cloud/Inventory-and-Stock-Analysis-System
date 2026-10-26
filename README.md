# Inventory and Stock Analysis System

A beginner-friendly full-stack inventory management application built with **Python Flask**, **SQLite**, HTML, CSS, and JavaScript.

## Features
- Dashboard with total products, inventory value, low-stock alerts, and out-of-stock count
- Add, edit, and delete products
- Track SKU, category, supplier, cost price, selling price, quantity, and reorder level
- Search and filter inventory
- Stock-in and stock-out transactions with quantity validation
- Stock movement history
- CSV export of current inventory
- Responsive layout

> This is a local learning/demo application. It does not include authentication or production-grade access controls. Add these before deploying it for real business use.

## Requirements
- Python 3.10+
- pip
- Git (for publishing to GitHub)

## Run locally

### macOS / Linux
```bash
cd Inventory-and-Stock-Analysis-System
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Windows PowerShell
```powershell
cd Inventory-and-Stock-Analysis-System
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser. Press `Ctrl+C` in the terminal to stop the server.

The SQLite database is created automatically at `instance/inventory.db` on first run.

## Project structure
```text
Inventory-and-Stock-Analysis-System/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── instance/                 # created automatically; database is not committed
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/
    ├── base.html
    ├── index.html
    ├── products.html
    ├── product_form.html
    ├── transactions.html
    └── transaction_form.html
```

## Git and GitHub
1. Create a new **empty** GitHub repository named `Inventory-and-Stock-Analysis-System` (do not initialize it with a README if you already have this project).
2. From this project folder:
```bash
git init
git add .
git commit -m "Initial commit: Inventory and Stock Analysis System"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/Inventory-and-Stock-Analysis-System.git
git push -u origin main
```
3. Replace `YOUR-USERNAME` with your GitHub username. If Git says `remote origin already exists`, use `git remote set-url origin https://github.com/YOUR-USERNAME/Inventory-and-Stock-Analysis-System.git`.
4. If prompted to authenticate, complete GitHub's browser sign-in or use a configured credential manager / SSH key. Do not put passwords or access tokens into source code.

## Troubleshooting
- `python` not found: try `python3` on macOS/Linux or `py` on Windows.
- Port 5000 busy: stop the other app or change `app.run(port=5001)` at the bottom of `app.py`.
- Git identity missing:
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```
Use the name/email you want associated with commits.
