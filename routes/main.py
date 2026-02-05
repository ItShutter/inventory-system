from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from models import Product, Customer, Supplier, Transaction, SystemConfig, db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    query = request.args.get('q')
    if query:
        products = Product.query.filter(Product.name.contains(query) | Product.sku.contains(query)).all()
    else:
        products = Product.query.all()

    # --- ส่วนสถิติ Dashboard ---
    total_products = Product.query.count()
    low_stock = Product.query.filter(Product.current_quantity < 5).count()
    out_of_stock = Product.query.filter(Product.current_quantity == 0).count()
    total_quantity = db.session.query(func.sum(Product.current_quantity)).scalar() or 0
    
    # --- 1. กราฟวงกลม (Pie Chart) ---
    category_query = db.session.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
    cat_labels = [c[0] for c in category_query]
    cat_data = [c[1] for c in category_query]

    # --- 2. กราฟแท่ง (Bar Chart) ---
    top_query = db.session.query(Transaction.product_name, func.sum(Transaction.quantity))\
        .filter(Transaction.transaction_type == 'OUT')\
        .group_by(Transaction.product_name)\
        .order_by(func.sum(Transaction.quantity).desc())\
        .limit(5).all()
    
    top_labels = [t[0] for t in top_query]
    top_data = [t[1] for t in top_query]

    return render_template('index.html', 
                           products=products, 
                           total_products=total_products,
                           low_stock=low_stock, 
                           out_of_stock=out_of_stock,
                           total_quantity=total_quantity, 
                           customers=Customer.query.all(),
                           suppliers=Supplier.query.all(),
                           cat_labels=cat_labels, 
                           cat_data=cat_data,
                           top_labels=top_labels, 
                           top_data=top_data)

@main_bp.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    if request.method == 'POST':
        db.session.add(Customer(
            name=request.form['name'], 
            email=request.form['email'], 
            phone=request.form['phone'], 
            address=request.form['address']
        ))
        db.session.commit()
        return redirect(url_for('main.customers'))
    return render_template('customers.html', customers=Customer.query.all())

@main_bp.route('/suppliers', methods=['GET', 'POST'])
@login_required
def suppliers():
    if request.method == 'POST':
        db.session.add(Supplier(
            name=request.form['name'], 
            contact_person=request.form['contact_person'], 
            phone=request.form['phone'], 
            email=request.form['email'], 
            address=request.form['address']
        ))
        db.session.commit()
        return redirect(url_for('main.suppliers'))
    return render_template('suppliers.html', suppliers=Supplier.query.all())

@main_bp.route('/report')
@login_required
def report():
    # --- 1. เช็คสิทธิ์ Admin เป็นอันดับแรก (ย้ายมาไว้ตรงนี้) ---
    if current_user.role != 'admin':
        flash('สงวนสิทธิ์เฉพาะผู้ดูแลระบบ (Admin Only)', 'danger')
        return redirect(url_for('main.index'))
    # ----------------------------------------------------

    period = request.args.get('period', 'month') # Default เป็นเดือนนี้
    
    # สร้าง Query
    query = db.session.query(Transaction, Product).join(Product, Transaction.sku == Product.sku).filter(Transaction.transaction_type == 'OUT')
    
    # กรองตามวันที่เลือก
    if period == 'today':
        query = query.filter(func.date(Transaction.timestamp) == date.today())
    elif period == 'month':
        today = date.today()
        query = query.filter(func.strftime('%Y-%m', Transaction.timestamp) == today.strftime('%Y-%m'))
    # ถ้าเป็น 'all' ก็ไม่ต้อง filter อะไรเพิ่ม
    
    # ดึงข้อมูลและคำนวณ
    results = query.order_by(Transaction.timestamp.desc()).all()
    
    report_data = []
    total_sales = 0
    total_cost = 0
    
    for txn, prod in results:
        sales = txn.quantity * prod.selling_price
        cost = txn.quantity * prod.cost_price
        profit = sales - cost
        
        total_sales += sales
        total_cost += cost
        
        report_data.append({
            'timestamp': txn.timestamp,
            'product_name': prod.name,
            'sku': prod.sku,
            'quantity': txn.quantity,
            'cost': prod.cost_price,
            'price': prod.selling_price,
            'total_sales': sales,
            'profit': profit
        })
        
    total_profit = total_sales - total_cost

    return render_template('report.html', 
                           report_data=report_data,
                           total_sales=total_sales,
                           total_cost=total_cost,
                           total_profit=total_profit,
                           period=period)

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    # เช็คสิทธิ์ Admin
    if current_user.role != 'admin':
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('main.index'))

    keys = ['company_name', 'company_address', 'company_phone', 'tax_id', 'vat_rate', 'line_channel_access_token', 'line_user_id']

    if request.method == 'POST':
        for key in keys:
            val = request.form.get(key, '')
            conf = SystemConfig.query.filter_by(key=key).first()
            if conf:
                conf.value = val 
            else:
                new_conf = SystemConfig(key=key, value=val)
                db.session.add(new_conf)
        
        db.session.commit()
        flash('บันทึกการตั้งค่าเรียบร้อยแล้ว!', 'success')
        return redirect(url_for('main.settings'))

    configs = {c.key: c.value for c in SystemConfig.query.all()}
    return render_template('settings.html', config=configs)