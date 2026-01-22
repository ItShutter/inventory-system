-- ตารางที่ 1: Products (เก็บข้อมูลหลักของสินค้าและจำนวนคงเหลือปัจจุบัน)
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku VARCHAR(50) UNIQUE NOT NULL,       -- รหัสสินค้า (ห้ามซ้ำ)
    name VARCHAR(100) NOT NULL,            -- ชื่อสินค้า
    description TEXT,                      -- รายละเอียดเพิ่มเติม
    current_quantity INTEGER DEFAULT 0     -- จำนวนคงเหลือ (อัปเดตตลอดเวลา)
);

-- ตารางที่ 2: Transactions (เก็บประวัติการรับเข้าและขายออก)
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,           -- Foreign Key เชื่อมไปยังตาราง products
    transaction_type VARCHAR(10) NOT NULL, -- ประเภทรายการ: 'IN' (รับเข้า) หรือ 'OUT' (ขายออก)
    quantity INTEGER NOT NULL,             -- จำนวนที่ทำรายการ
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, -- เวลาที่เกิดรายการ
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);