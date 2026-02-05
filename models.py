from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='staff')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='General')
    description = db.Column(db.Text)
    current_quantity = db.Column(db.Integer, default=0)
    min_quantity = db.Column(db.Integer, default=5)  # ✅ เพิ่มจุดสั่งซื้อขั้นต่ำ (ค่าเริ่มต้น 5)
    cost_price = db.Column(db.Float, default=0.0)    # ราคาทุน
    selling_price = db.Column(db.Float, default=0.0) # ราคาขาย
    image_url = db.Column(db.String(500))
    
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    product_name = db.Column(db.String(100))
    sku = db.Column(db.String(50))
    transaction_type = db.Column(db.String(10)) # IN/OUT
    quantity = db.Column(db.Integer)
    user_name = db.Column(db.String(100))
    party_name = db.Column(db.String(100)) # Customer or Supplier Name

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)

class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)