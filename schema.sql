CREATE DATABASE IF NOT EXISTS inventory_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE inventory_db;

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    contact_name VARCHAR(120),
    email VARCHAR(160),
    phone VARCHAR(40),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(60) NOT NULL UNIQUE,
    product_name VARCHAR(160) NOT NULL,
    category VARCHAR(100),
    reorder_level INT NOT NULL DEFAULT 0,
    unit_cost DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    opening_stock INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_reorder_nonnegative CHECK (reorder_level >= 0),
    CONSTRAINT chk_cost_nonnegative CHECK (unit_cost >= 0),
    CONSTRAINT chk_opening_nonnegative CHECK (opening_stock >= 0)
);

CREATE TABLE IF NOT EXISTS stock_transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type ENUM('IN','OUT','ADJUSTMENT') NOT NULL,
    quantity INT NOT NULL,
    supplier_id INT NULL,
    note VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transaction_product FOREIGN KEY (product_id)
      REFERENCES products(product_id),
    CONSTRAINT fk_transaction_supplier FOREIGN KEY (supplier_id)
      REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
    CONSTRAINT chk_transaction_quantity CHECK (quantity > 0 OR transaction_type = 'ADJUSTMENT'),
    INDEX idx_transaction_product_date (product_id, transaction_date)
);

-- Optional demo data. Run only once if you want sample records.
INSERT IGNORE INTO suppliers (supplier_id, supplier_name, contact_name, email, phone)
VALUES
(1, 'Bright Office Supplies', 'Maya Rao', 'maya@example.com', '9000000001'),
(2, 'Campus Tech Traders', 'Arun Das', 'arun@example.com', '9000000002');

INSERT IGNORE INTO products
(sku, product_name, category, reorder_level, unit_cost, opening_stock)
VALUES
('PEN-001', 'Blue Ball Pen', 'Stationery', 20, 5.50, 100),
('NOTE-001', 'Notebook A4', 'Stationery', 15, 42.00, 50),
('USB-001', 'USB Drive 32GB', 'Electronics', 5, 350.00, 12);
