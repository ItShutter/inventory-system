import os
from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'MySuperSecretKey2026')
    
    # --- เปลี่ยนจาก SQLite เป็น PostgreSQL ตรงนี้ครับ ---
    # รูปแบบ: postgresql://username:password@host:port/database_name
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI', 
        'postgresql://admin:mysecretpassword@localhost:5432/inventory_system'
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}