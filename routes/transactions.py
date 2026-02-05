from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
# ต้อง import SystemConfig เพื่อใช้ดึงชื่อบริษัทในใบเสร็จ
from models import Product, Transaction, Customer, SystemConfig

transactions_bp = Blueprint('transactions', __name__)

# --- 1. ฟังก์ชันตัด/เพิ่มสต็อก (IN/OUT) ---
@transactions_bp.route('/update_stock/<int:product_id>', methods=['POST'])
@login_required
def update_stock(product_id):
    product = Product.query.get_or_404(product_id)
    type = request.form['type']
    qty = int(request.form['quantity'])
    party = request.form.get('party_name', '-')

    # เช็คก่อนว่าของพอขายไหม
    if type == 'OUT' and product.current_quantity < qty:
        flash('Error: สินค้าไม่พอให้ตัดสต็อก!', 'danger')
        return redirect(url_for('main.index'))
    
    if type == 'IN': 
        product.current_quantity += qty
    elif type == 'OUT': 
        product.current_quantity -= qty

    db.session.add(Transaction(
        product_name=product.name, 
        sku=product.sku, 
        transaction_type=type,
        quantity=qty, 
        user_name=current_user.username, 
        party_name=party
    ))
    db.session.commit()
    flash('อัปเดตสต็อกเรียบร้อยแล้ว', 'success')
    return redirect(url_for('main.index'))

# --- 2. ฟังก์ชันดูประวัติ (History) ---
@transactions_bp.route('/history')
@login_required
def history():
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    return render_template('history.html', transactions=transactions)

# --- 3. ฟังก์ชันพิมพ์ใบเสร็จ (Invoice) ---
@transactions_bp.route('/print_invoice/<int:id>')
@login_required
def print_invoice(id):
    t = Transaction.query.get_or_404(id)
    product = Product.query.filter_by(sku=t.sku).first()
    
    customer = None
    if t.transaction_type == 'OUT':
        customer = Customer.query.filter_by(name=t.party_name).first()
    
    # ดึงค่า Config บริษัท (ชื่อ/ที่อยู่) ส่งไปที่หน้าใบเสร็จ
    try:
        sys_conf = {c.key: c.value for c in SystemConfig.query.all()}
    except:
        sys_conf = {}

    return render_template('invoice.html', t=t, customer=customer, product=product, conf=sys_conf)

# --- 4. ฟังก์ชันปรับปรุงยอดสต็อก (Adjust Stock) ---
# (อันนี้ที่คุณเพิ่งเพิ่มมา ต้องใส่ไว้ด้วยนะครับ ไม่งั้นปุ่มประแจจะพัง)
@transactions_bp.route('/adjust_stock/<int:product_id>', methods=['POST'])
@login_required
def adjust_stock(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        actual_qty = int(request.form['actual_quantity'])
        reason = request.form.get('note', 'Audit')

        diff = actual_qty - product.current_quantity

        if diff == 0:
            return redirect(url_for('main.index'))

        product.current_quantity = actual_qty

        db.session.add(Transaction(
            product_name=product.name,
            sku=product.sku,
            transaction_type='ADJUST', 
            quantity=diff, 
            user_name=current_user.username, 
            party_name=reason 
        ))
        db.session.commit()
        flash(f'ปรับยอดสต็อกเรียบร้อย (ผลต่าง: {diff:+d})', 'warning')

    except ValueError:
        flash('กรุณาระบุจำนวนตัวเลขที่ถูกต้อง', 'danger')
        
    return redirect(url_for('main.index'))