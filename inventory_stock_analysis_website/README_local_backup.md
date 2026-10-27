# StockWise — Inventory and Stock Analysis System

Flask + MySQL academic project for product/supplier management, stock-in/stock-out transactions, low-stock alerts, stock valuation, movement analytics and CSV export.

## Open the project

- **GitHub source code:** `https://github.com/ShaikAnjuma001/inventory-stock-analysis`
- **Live website:** After deployment, copy the public URL provided by Render into this README. A GitHub repository URL displays source code; it does not execute a Flask application.

## Deploy from the GitHub repository

This project includes `render.yaml` to prefill the Render web-service configuration.

1. Push the project files to the `main` branch of your GitHub repository.
2. Create or sign in to an account at https://render.com/.
3. In Render, choose **New → Blueprint** (or create a Web Service from the repository).
4. Connect GitHub and choose `ShaikAnjuma001/inventory-stock-analysis`.
5. Render reads `render.yaml`. Confirm the service settings and deploy.
6. **Set up an external hosted MySQL database** reachable from Render. Render's web service does not automatically create a MySQL database for this configuration.
7. In the Render service's **Environment** settings, set:
   - `DB_HOST`: database hostname
   - `DB_PORT`: database port, normally `3306`
   - `DB_USER`: database username
   - `DB_PASSWORD`: database password
   - `DB_NAME`: database name
   - `DB_SSL`: keep `true` if your database provider requires SSL; otherwise set it according to provider instructions.
8. Run `schema_cloud.sql` (or `schema.sql` if appropriate for your database) against the hosted database. Check that the SQL schema matches the tables expected by `app.py`.
9. Wait for deployment to finish. Open the public `onrender.com` URL shown by Render.
10. Edit the **Live website** line above in this README and commit/push it, so visitors can open the app directly from the repository page.

**Important:** Deployment is not complete until a reachable hosted MySQL database is configured and the public URL is tested. Do not commit passwords or `.env` files. GitHub Pages cannot run this Flask + MySQL backend.

## Run locally in VS Code (Windows PowerShell)

1. Install Python 3.10+ and MySQL Server/Workbench.
2. Open this folder in VS Code.
3. Open `schema.sql` in MySQL Workbench and execute it on your local MySQL server.
4. In the VS Code terminal:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

5. Set the local database environment variables (replace the password):

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

7. Open `http://127.0.0.1:5000`.

## GitHub push commands

Run from this project folder:

```powershell
git status
git add .
git commit -m "Prepare StockWise for online deployment"
git branch -M main
git remote -v
```

If no remote named `origin` exists:

```powershell
git remote add origin https://github.com/ShaikAnjuma001/inventory-stock-analysis.git
```

If `origin` already exists:

```powershell
git remote set-url origin https://github.com/ShaikAnjuma001/inventory-stock-analysis.git
```

Then push:

```powershell
git push -u origin main
```

If push is rejected, inspect `git status` and reconcile remote/local commits before retrying; don't overwrite remote history blindly.

## Features

- Product and supplier management
- Stock-in and stock-out history
- Prevent stock-out from making inventory negative
- Low-stock alerts using reorder levels
- Estimated stock valuation
- Pandas/NumPy movement analysis
- Matplotlib stock chart
- CSV report download

## Academic scope

Reorder recommendations are advisory; the app does not automatically purchase stock. Total stock-out is a movement indicator and is not necessarily verified sales.
