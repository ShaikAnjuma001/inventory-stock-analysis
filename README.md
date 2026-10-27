# StockWise - Inventory and Stock Analysis System

Flask website for tracking stock movements, flagging low-stock items, and analysing product movement and inventory value.
Stack: Flask, MySQL (PyMySQL), Pandas, NumPy, Matplotlib.

## Live Website

[**Open StockWise — Inventory and Stock Analysis System**](https://inventory-stock-analysis-q2az.onrender.com)

**Source Code:** https://github.com/ShaikAnjuma001/inventory-stock-analysis
## Features
- Products (SKU, category, opening balance, reorder level, unit cost) and suppliers
- Stock in, stock out, and logged adjustments (adjustments require a reason)
- Current stock = opening balance + all transactions (calculated, never typed in)
- Stock out and adjustments that would make stock negative are rejected (row is locked while checking)
- Low-stock list with suggested order quantity (recommendation only, no automatic purchasing)
- Fast-moving products and days-of-stock-left (Pandas + NumPy)
- Estimated inventory value, overall and by category
- Reconciliation report: rebuilds every balance from history and checks it never went below zero
- Matplotlib charts: stock vs reorder level, monthly movement
- CSV export of stock, low-stock and transaction history

## Database
`products`, `suppliers`, `stock_transactions` (see `schema.sql`, includes sample data).
Transaction types: `IN`, `OUT`, `ADJUST_IN`, `ADJUST_OUT`. Products and transactions are never deleted, so history always reconciles.

## Run locally (Windows / PowerShell)
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
Run `schema.sql` in MySQL Workbench, then:
```
$env:DB_HOST="localhost"; $env:DB_PORT="3306"; $env:DB_USER="root"
$env:DB_PASSWORD="YOUR_MYSQL_PASSWORD"; $env:DB_NAME="inventory_db"
python app.py
```
**Live Website:** https://inventory-stock-analysis-q2az.onrender.com

## Deploy on PythonAnywhere (free)
1. Bash console: `git clone <your repo url>`, then `mkvirtualenv myenv --python=/usr/bin/python3.10` and `pip install -r requirements.txt`.
2. Databases tab: set a MySQL password, create `inventory_db` (real name `USERNAME$inventory_db`).
3. Delete the `CREATE DATABASE` and `USE` lines from `schema.sql`, then run:
   `mysql -u USERNAME -h USERNAME.mysql.pythonanywhere-services.com -p 'USERNAME$inventory_db' < schema.sql`
4. Web tab: Add a new web app, Manual configuration. Set source code and working directory to the cloned folder, and virtualenv to `/home/USERNAME/.virtualenvs/myenv`.
5. WSGI file:
```python
import sys, os
path = '/home/USERNAME/stockwise'
if path not in sys.path: sys.path.insert(0, path)
os.environ['DB_HOST'] = 'USERNAME.mysql.pythonanywhere-services.com'
os.environ['DB_PORT'] = '3306'
os.environ['DB_USER'] = 'USERNAME'
os.environ['DB_PASSWORD'] = 'YOUR_MYSQL_PASSWORD'
os.environ['DB_NAME'] = 'USERNAME$inventory_db'
os.environ['SECRET_KEY'] = 'any-long-random-text'
from app import app as application
```
6. Click Reload. Site: https://USERNAME.pythonanywhere.com

## Acceptance criteria
| Requirement | Where |
|---|---|
| Stock cannot silently become negative | `add_transaction()` in `app.py` blocks it and shows the available quantity |
| All adjustments are logged | `ADJUST_IN` / `ADJUST_OUT` rows with a mandatory note, visible in Stock movements |
| History reconciles with current stock | Reports page, Reconciliation check |
| Current stock report, low-stock list, chart, inventory value | Reports and Dashboard |
