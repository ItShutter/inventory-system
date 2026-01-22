import os 
import pandas as pd
import io
from flask import send_file
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func

# 1. Setup & Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SECRET_KEY'] = 'mysecretkey'

# --- ตั้งค่าการอัปโหลดรูปภาพ ---
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# --- ตั้งค่า Login Manager ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# -----------------------------------------
# 2. Database Models
# -----------------------------------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50), default='General') 
    description = db.Column(db.Text)
    current_quantity = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(500))

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

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    product_name = db.Column(db.String(100))
    sku = db.Column(db.String(50))
    transaction_type = db.Column(db.String(10))
    quantity = db.Column(db.Integer)
    user_name = db.Column(db.String(100))
    party_name = db.Column(db.String(100))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20), default='staff')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------------------
# 3. Routes & Logic
# -----------------------------------------

with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@login_required
def index():
    query = request.args.get('q')
    
    if query:
        products = Product.query.filter(
            Product.name.contains(query) | 
            Product.sku.contains(query) | 
            Product.category.contains(query) 
        ).all()
    else:
        products = Product.query.all()

    # 1. ข้อมูลพื้นฐาน
    total_products = Product.query.count()
    low_stock = Product.query.filter(Product.current_quantity < 5).count()
    out_of_stock = Product.query.filter(Product.current_quantity == 0).count()
    total_quantity = db.session.query(func.sum(Product.current_quantity)).scalar() or 0
    
    # 2. เตรียมข้อมูลสำหรับ Dropdown
    customers = Customer.query.all()
    suppliers = Supplier.query.all()

    # 3. เตรียมข้อมูลสำหรับ "กราฟ" (เพิ่มใหม่!) 📊
    # กราฟแท่ง: ชื่อสินค้า และ จำนวน
    product_names = [p.name for p in products]
    product_quantities = [p.current_quantity for p in products]

    # ส่งตัวแปรทั้งหมดไปหน้าเว็บ
    return render_template('index.html', 
                           products=products, 
                           total_products=total_products, 
                           low_stock=low_stock,
                           out_of_stock=out_of_stock,
                           total_quantity=total_quantity,
                           customers=customers,
                           suppliers=suppliers,
                           # ส่งข้อมูลกราฟ
                           product_names=product_names,
                           product_quantities=product_quantities)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'admin':
        return "Access Denied", 403
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form['sku']
        category = request.form['category'] # 👈 รับค่า category
        description = request.form.get('description', '')
        
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                image_filename = unique_filename

        new_product = Product(
            name=name, 
            sku=sku, 
            category=category, # 👈 บันทึกลง DB
            description=description, 
            current_quantity=0, 
            image_url=image_filename
        )
        
        try:
            db.session.add(new_product)
            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
             return f"Error adding product: {e}"
            
    return render_template('add_product.html')

@app.route('/update_stock/<int:product_id>', methods=['POST'])
@login_required
def update_stock(product_id):
    # ✅ ไม่ต้องมีเช็ค role ตรงนี้ เพราะ Staff ต้องใช้ฟังก์ชันนี้ได้
    product = Product.query.get_or_404(product_id)
    type = request.form['type']
    quantity = int(request.form['quantity'])
    party_name = request.form.get('party_name', '-')

    if type == 'IN':
        product.current_quantity += quantity
    elif type == 'OUT':
        if product.current_quantity >= quantity:
            product.current_quantity -= quantity
        else:
            pass 

    new_transaction = Transaction(
        product_name=product.name,
        sku=product.sku,
        transaction_type=type,
        quantity=quantity,
        user_name=current_user.username,
        party_name=party_name
    )
    db.session.add(new_transaction)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/product/<int:product_id>')
@login_required
def product_detail(product_id):
    # ✅ Staff ควรเข้าดูรายละเอียดสินค้าได้
    product = Product.query.get_or_404(product_id)
    history = Transaction.query.filter_by(sku=product.sku).order_by(Transaction.timestamp.desc()).all()
    return render_template('product_detail.html', product=product, history=history)

@app.route('/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    # 🔒 ย้ายมาไว้ข้างใน
    if current_user.role != 'admin':
        return "Access Denied: You are not Admin!", 403

    product = Product.query.get_or_404(product_id)
    
    try:
        Transaction.query.filter_by(sku=product.sku).delete()
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error deleting product: {e}"
    
@app.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    # 🔒 1. เช็คสิทธิ์ Admin
    if current_user.role != 'admin':
        return "Access Denied: You are not Admin!", 403

    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        # 2. รับค่าจากฟอร์ม
        product.sku = request.form['sku']
        product.name = request.form['name']
        product.category = request.form['category']
        product.description = request.form['description']
        
        # 3. จัดการรูปภาพ (ถ้ามีการอัปโหลดใหม่)
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                product.image_url = unique_filename
        
        # 4. บันทึกข้อมูล
        try:
            db.session.commit()
            return redirect(url_for('index'))
        except:
            return "Error updating product."

    return render_template('edit_product.html', product=product)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password")
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/export')
@login_required
def export_data():
    products = Product.query.all()
    data = []
    for p in products:
        data.append({
            'SKU': p.sku,
            'Name': p.name,
            'Quantity': p.current_quantity,
            'Description': p.description,
            'Image': p.image_url
        })
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Stock')
    
    output.seek(0)
    return send_file(output, download_name="inventory_stock.xlsx", as_attachment=True)

@app.route('/import', methods=['POST'])
@login_required
def import_data():
    if current_user.role != 'admin':
        return "Access Denied", 403

    file = request.files['file']
    if not file:
        return "No file uploaded", 400
        
    try:
        df = pd.read_excel(file)
        
        for index, row in df.iterrows():
            sku = str(row['SKU'])
            product = Product.query.filter_by(sku=sku).first()
            cat = row.get('Category', 'General')
            
            if product:
                product.current_quantity = row['Quantity']
                product.name = row['Name']
                product.category = cat
            else:
                new_product = Product(
                    sku=sku,
                    name=row['Name'],
                    category=cat,
                    current_quantity=row['Quantity'],
                    description=row.get('Description', ''),
                    image_url=row.get('Image', None)
                )
                db.session.add(new_product)
        
        db.session.commit()
        return redirect(url_for('index'))
        
    except Exception as e:
        return f"Error importing file: {e}"
    
@app.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        
        new_customer = Customer(name=name, email=email, phone=phone, address=address)
        db.session.add(new_customer)
        db.session.commit()
        return redirect(url_for('customers'))

    all_customers = Customer.query.all()
    return render_template('customers.html', customers=all_customers)

@app.route('/suppliers', methods=['GET', 'POST'])
@login_required
def suppliers():
    if request.method == 'POST':
        name = request.form['name']
        contact_person = request.form['contact_person']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        
        new_supplier = Supplier(name=name, contact_person=contact_person, 
                                phone=phone, email=email, address=address)
        db.session.add(new_supplier)
        db.session.commit()
        return redirect(url_for('suppliers'))

    all_suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=all_suppliers)

@app.route('/history')
@login_required
def history():
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    return render_template('history.html', transactions=transactions)

# --- Route: พิมพ์ใบเสร็จ / ใบส่งของ ---
@app.route('/print_invoice/<int:transaction_id>')
@login_required
def print_invoice(transaction_id):
    # 1. ดึงข้อมูล Transaction นั้นๆ มา
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # 2. หาข้อมูลลูกค้าเพิ่มเติม (ที่อยู่/เบอร์โทร) โดยค้นหาจากชื่อ
    # (ระบบเราเก็บ party_name เป็นชื่อลูกค้าไว้)
    customer_info = None
    if transaction.transaction_type == 'OUT':
        customer_info = Customer.query.filter_by(name=transaction.party_name).first()
        
    # 3. ส่งข้อมูลไปหน้า invoice
    return render_template('invoice.html', t=transaction, customer=customer_info)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
        # 1. สร้าง Admin (ถ้ายังไม่มี)
        if not User.query.filter_by(username='admin').first():
            hashed_pw = generate_password_hash('1234')
            # กำหนด role='admin'
            admin = User(username='admin', password=hashed_pw, role='admin') 
            db.session.add(admin)
            db.session.commit()
            print("Admin user created!")

        # 2. สร้าง Staff (พนักงาน)
        if not User.query.filter_by(username='staff').first():
            hashed_pw = generate_password_hash('1234')
            # กำหนด role='staff'
            staff = User(username='staff', password=hashed_pw, role='staff')
            db.session.add(staff)
            db.session.commit()
            print("Staff user created! (User: staff / Pass: 1234)")
             
        app.run(host='0.0.0.0', port=5000, debug=True)
