#!/usr/bin/env bash
# Starts MySQL (if stopped) and the website in a GitHub Codespace
sudo service mariadb start 2>/dev/null || sudo service mysql start 2>/dev/null || true
export DB_HOST=127.0.0.1 DB_PORT=3306 DB_USER=stock DB_PASSWORD=stock123 DB_NAME=inventory_db
python app.py
