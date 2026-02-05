import sqlite3
import os

# หาตำแหน่งไฟล์ Database ให้อัตโนมัติ (แก้ปัญหาหาไฟล์ไม่เจอ)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_paths = [
    os.path.join(BASE_DIR, 'instance', 'inventory.db'), # แบบ Flask มาตรฐาน
    os.path.join(BASE_DIR, 'inventory.db')              # แบบวางหน้าแรก
]

target_db = None
for path in db_paths:
    if os.path.exists(path):
        target_db = path
        break

if not target_db:
    print("❌ ไม่พบไฟล์ฐานข้อมูล inventory.db เลย! (คุณเคยรัน app.py หรือยัง?)")
else:
    print(f"⚡ กำลังเชื่อมต่อฐานข้อมูลที่: {target_db}")
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()

    try:
        # เพิ่มคอลัมน์ min_quantity
        try:
            cursor.execute("ALTER TABLE product ADD COLUMN min_quantity INTEGER DEFAULT 5")
            print("✅ เพิ่มคอลัมน์ min_quantity สำเร็จ!")
        except sqlite3.OperationalError:
            print("⚠️ มีคอลัมน์ min_quantity อยู่แล้ว (ข้าม)")

        # เพิ่มคอลัมน์ cost_price (เผื่อใครยังไม่มี)
        try:
            cursor.execute("ALTER TABLE product ADD COLUMN cost_price FLOAT DEFAULT 0.0")
            print("✅ เพิ่มคอลัมน์ cost_price สำเร็จ!")
        except sqlite3.OperationalError:
            pass

        # เพิ่มคอลัมน์ selling_price (เผื่อใครยังไม่มี)
        try:
            cursor.execute("ALTER TABLE product ADD COLUMN selling_price FLOAT DEFAULT 0.0")
            print("✅ เพิ่มคอลัมน์ selling_price สำเร็จ!")
        except sqlite3.OperationalError:
            pass

        conn.commit()
        print("🎉 อัปเดตฐานข้อมูลเรียบร้อย! พร้อมใช้งาน")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        conn.close()