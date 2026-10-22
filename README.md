# StockWise — Inventory and Stock Analysis System

A Flask website for an academic inventory-management project. It uses MySQL for persistent data, Pandas and NumPy for analysis, and Matplotlib for a stock chart.

## Features
- Dashboard with product count, available units, inventory valuation and low-stock alerts
- Product and supplier management
- Stock-in / stock-out transaction history
- Stock-out validation to prevent negative inventory
- Low-stock report and CSV export
- Matplotlib chart, with Pandas/NumPy calculations

## Requirements
- Python 3.10+
- MySQL Server
- VS Code (recommended)

## Run locally
1. Open this folder in VS Code.
2. Start MySQL Server.
3. Open `schema.sql` in MySQL Workbench and execute it.
4. In the VS Code terminal, run:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```
5. Set database settings in PowerShell (replace the password):
   ```powershell
   $env:DB_HOST="localhost"
   $env:DB_PORT="3306"
   $env:DB_USER="root"
   $env:DB_PASSWORD="YOUR_MYSQL_PASSWORD"
   $env:DB_NAME="inventory_db"
   ```
6. Start the website:
   ```powershell
   python app.py
   ```
7. Open `http://127.0.0.1:5000` in your browser.

## Deployment note
To publish this online, push the project to GitHub and deploy it on a Python web host such as Render. You also need a hosted MySQL database reachable by the web host. Configure `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, and `SECRET_KEY` as environment variables in the hosting service. Do not commit passwords or database credentials to GitHub. Set the web service start command to `gunicorn app:app`. Confirm current hosting/database pricing and availability before choosing a provider.

## Academic scope
Reorder recommendations use configurable reorder levels. The app does not place purchase orders automatically. `total stock-out` is a movement indicator, not necessarily verified sales.
