-- StockWise schema + sample data.
-- PythonAnywhere free plan: DELETE the next two lines (CREATE DATABASE / USE) before running.
CREATE DATABASE IF NOT EXISTS inventory_db;
USE inventory_db;

DROP TABLE IF EXISTS stock_transactions;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS suppliers;

CREATE TABLE suppliers (
  supplier_id   INT AUTO_INCREMENT PRIMARY KEY,
  supplier_name VARCHAR(100) NOT NULL UNIQUE,
  contact_email VARCHAR(120)
);

CREATE TABLE products (
  product_id      INT AUTO_INCREMENT PRIMARY KEY,
  sku             VARCHAR(30)  NOT NULL UNIQUE,
  product_name    VARCHAR(120) NOT NULL,
  category        VARCHAR(60)  NOT NULL,
  opening_balance INT NOT NULL DEFAULT 0,
  reorder_level   INT NOT NULL DEFAULT 10,
  unit_cost       DECIMAL(10,2) NOT NULL,
  CHECK (opening_balance >= 0), CHECK (reorder_level >= 0), CHECK (unit_cost >= 0)
);

-- IN / OUT = normal movements; ADJUST_IN / ADJUST_OUT = logged corrections (note required by the app)
CREATE TABLE stock_transactions (
  transaction_id   INT AUTO_INCREMENT PRIMARY KEY,
  product_id       INT NOT NULL,
  transaction_date DATE NOT NULL,
  transaction_type ENUM('IN','OUT','ADJUST_IN','ADJUST_OUT') NOT NULL,
  quantity         INT NOT NULL,
  supplier_id      INT NULL,
  note             VARCHAR(255),
  created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK (quantity > 0),
  FOREIGN KEY (product_id)  REFERENCES products(product_id),
  FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

INSERT INTO suppliers (supplier_name, contact_email) VALUES
 ('TechSource Distributors','sales@techsource.example'),
 ('OfficeMart Wholesale','orders@officemart.example'),
 ('HomeWorks Supplies','info@homeworks.example');

INSERT INTO products (sku, product_name, category, opening_balance, reorder_level, unit_cost) VALUES
 ('SKU-1001','Wireless Mouse','Electronics',40,20,450.00),
 ('SKU-1002','USB Keyboard','Electronics',30,15,700.00),
 ('SKU-1003','A4 Paper Ream','Stationery',100,50,260.00),
 ('SKU-1004','Ballpoint Pens (box)','Stationery',60,25,90.00),
 ('SKU-1005','Notebook','Stationery',80,40,55.00),
 ('SKU-1006','HDMI Cable','Electronics',25,10,220.00),
 ('SKU-1007','Desk Lamp','Furniture',15,8,850.00),
 ('SKU-1008','Stapler','Stationery',20,10,120.00);

INSERT INTO stock_transactions (product_id, transaction_date, transaction_type, quantity, supplier_id, note) VALUES
 (1,'2026-08-05','IN',20,1,'Restock'),
 (1,'2026-08-20','OUT',15,NULL,'Sales order'),
 (1,'2026-09-12','OUT',18,NULL,'Sales order'),
 (1,'2026-10-10','OUT',12,NULL,'Sales order'),
 (2,'2026-08-18','OUT',8,NULL,'Sales order'),
 (2,'2026-09-15','OUT',9,NULL,'Sales order'),
 (2,'2026-10-14','OUT',5,NULL,'Sales order'),
 (3,'2026-08-08','OUT',30,NULL,'Office issue'),
 (3,'2026-09-02','OUT',35,NULL,'Office issue'),
 (3,'2026-09-20','IN',40,2,'Restock'),
 (3,'2026-10-12','OUT',20,NULL,'Office issue'),
 (4,'2026-08-25','OUT',20,NULL,'Office issue'),
 (4,'2026-09-25','OUT',15,NULL,'Office issue'),
 (4,'2026-10-18','OUT',15,NULL,'Office issue'),
 (5,'2026-08-14','OUT',15,NULL,'Sales order'),
 (5,'2026-09-10','OUT',10,NULL,'Sales order'),
 (5,'2026-10-05','IN',25,2,'Restock'),
 (6,'2026-09-05','OUT',8,NULL,'Sales order'),
 (6,'2026-10-08','OUT',4,NULL,'Sales order'),
 (7,'2026-08-30','OUT',3,NULL,'Sales order'),
 (7,'2026-09-18','IN',5,3,'Restock'),
 (7,'2026-10-15','OUT',2,NULL,'Sales order'),
 (8,'2026-09-08','OUT',6,NULL,'Office issue'),
 (8,'2026-10-02','OUT',5,NULL,'Office issue'),
 (8,'2026-10-20','ADJUST_OUT',2,NULL,'Damaged units found during stock count');
