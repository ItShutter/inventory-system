import sqlite3
import os

# หาตำแหน่งไฟล์ Database
db_path = 'instance/inventory.db'
if not os.path.exists(db_path):
    db_path = 'inventory.db'

print(f"Connecting to database at: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # สร้างตาราง system_config
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT
    )
    """)
    print("✅ สร้างตาราง system_config สำเร็จ")
    
    # เพิ่มค่าเริ่มต้น (ถ้ายังไม่มี)
    default_configs = [
        ('company_name', 'ItShutter Inventory'),
        ('company_address', '123 Tech Street, Bangkok, Thailand'),
        ('company_phone', '02-123-4567'),
        ('tax_id', '0123456789000'),
        ('vat_rate', '7'),
        ('line_channel_access_token', ''),
        ('line_user_id', '')
    ]
    
    for key, val in default_configs:
        try:
            cursor.execute("INSERT INTO system_config (key, value) VALUES (?, ?)", (key, val))
            print(f"   + เพิ่มค่าเริ่มต้น: {key}")
        except sqlite3.IntegrityError:
            pass # มีอยู่แล้วข้ามไป

    conn.commit()
    print("🎉 อัปเดตฐานข้อมูลเรียบร้อย!")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()