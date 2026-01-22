from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    current_quantity = db.Column(db.Integer, default=0)

    # สร้างความสัมพันธ์เพื่อให้เรียกดูประวัติได้ง่าย (เช่น product.transactions)
    transactions = db.relationship('Transaction', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name} ({self.sku})>'

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'IN' or 'OUT'
    quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.quantity} for Product ID {self.product_id}>'