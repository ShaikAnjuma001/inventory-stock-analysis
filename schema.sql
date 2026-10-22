CREATE DATABASE IF NOT EXISTS inventory_db;
USE inventory_db;

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    phone VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(30) UNIQUE NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    opening_stock INT NOT NULL DEFAULT 0,
    reorder_level INT NOT NULL DEFAULT 10,
    unit_cost DECIMAL(10,2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS stock_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    transaction_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transaction_type ENUM('IN','OUT') NOT NULL,
    quantity INT NOT NULL,
    supplier_id INT NULL,
    CONSTRAINT fk_transaction_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT fk_transaction_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    CONSTRAINT chk_quantity_positive CHECK (quantity > 0)
);

-- Optional sample data: run this section only once.
INSERT IGNORE INTO suppliers (supplier_id, supplier_name, phone) VALUES
(1, 'ABC Suppliers', '9876543210'),
(2, 'Global Traders', '9876501234');

INSERT IGNORE INTO products
(product_id, sku, product_name, category, opening_stock, reorder_level, unit_cost) VALUES
(1, 'P001', 'Laptop', 'Electronics', 20, 5, 45000),
(2, 'P002', 'Mouse', 'Accessories', 50, 10, 500),
(3, 'P003', 'Keyboard', 'Accessories', 30, 8, 800),
(4, 'P004', 'Monitor', 'Electronics', 15, 5, 8000),
(5, 'P005', 'USB Cable', 'Accessories', 25, 10, 150);

INSERT INTO stock_transactions (product_id, transaction_type, quantity, supplier_id)
SELECT 1, 'IN', 5, 1 WHERE NOT EXISTS
(SELECT 1 FROM stock_transactions WHERE product_id=1 AND transaction_type='IN' AND quantity=5);
INSERT INTO stock_transactions (product_id, transaction_type, quantity, supplier_id)
SELECT 1, 'OUT', 18, NULL WHERE NOT EXISTS
(SELECT 1 FROM stock_transactions WHERE product_id=1 AND transaction_type='OUT' AND quantity=18);
INSERT INTO stock_transactions (product_id, transaction_type, quantity, supplier_id)
SELECT 2, 'IN', 20, 2 WHERE NOT EXISTS
(SELECT 1 FROM stock_transactions WHERE product_id=2 AND transaction_type='IN' AND quantity=20);
INSERT INTO stock_transactions (product_id, transaction_type, quantity, supplier_id)
SELECT 2, 'OUT', 55, NULL WHERE NOT EXISTS
(SELECT 1 FROM stock_transactions WHERE product_id=2 AND transaction_type='OUT' AND quantity=55);
INSERT INTO stock_transactions (product_id, transaction_type, quantity, supplier_id)
SELECT 3, 'OUT', 10, NULL WHERE NOT EXISTS
(SELECT 1 FROM stock_transactions WHERE product_id=3 AND transaction_type='OUT' AND quantity=10);
INSERT INTO stock_transactions (product_id, transaction_type, quantity, supplier_id)
SELECT 4, 'IN', 5, 1 WHERE NOT EXISTS
(SELECT 1 FROM stock_transactions WHERE product_id=4 AND transaction_type='IN' AND quantity=5);
INSERT INTO stock_transactions (product_id, transaction_type, quantity, supplier_id)
SELECT 4, 'OUT', 12, NULL WHERE NOT EXISTS
(SELECT 1 FROM stock_transactions WHERE product_id=4 AND transaction_type='OUT' AND quantity=12);
INSERT INTO stock_transactions (product_id, transaction_type, quantity, supplier_id)
SELECT 5, 'OUT', 10, NULL WHERE NOT EXISTS
(SELECT 1 FROM stock_transactions WHERE product_id=5 AND transaction_type='OUT' AND quantity=10);
