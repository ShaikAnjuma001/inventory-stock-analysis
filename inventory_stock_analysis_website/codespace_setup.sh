#!/usr/bin/env bash
# Run ONCE in a GitHub Codespace terminal:  bash codespace_setup.sh
set -e
echo ">> Installing MariaDB (MySQL-compatible)..."
sudo apt-get update -y
sudo apt-get install -y mariadb-server
sudo service mariadb start || sudo service mysql start
sleep 3

echo ">> Creating database, tables and sample data..."
sudo mysql < schema.sql
sudo mysql -e "CREATE USER IF NOT EXISTS 'stock'@'localhost' IDENTIFIED BY 'stock123';
               GRANT ALL PRIVILEGES ON inventory_db.* TO 'stock'@'localhost';
               FLUSH PRIVILEGES;"

echo ">> Installing Python packages..."
python -m pip install -r requirements.txt

echo ">> Done. Now run:  bash run.sh"
