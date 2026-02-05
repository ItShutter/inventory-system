import os, io, pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, current_app, send_file, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from extensions import db
from models import Product, Transaction, Category

products_bp = Blueprint('products', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def delete_image(filename):
    if filename:
        path = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

@products_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'admin': return "Access Denied", 403
    
    if request.method == 'POST':
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                fname = secure_filename(file.filename)
                image_filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + fname
                # สร้าง folder ถ้ายังไม่มี
                os.makedirs(os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER']), exist_ok=True)
                file.save(os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], image_filename))

        db.session.add(Product(
            name=request.form['name'], 
            sku=request.form['sku'],
            category=request.form['category'], 
            cost_price=float(request.form.get('cost_price', 0)),
            selling_price=float(request.form.get('selling_price', 0)),
            description=request.form.get('description',''),
            image_url=image_filename
        ))
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('add_product.html', categories=Category.query.all())

@products_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if current_user.role != 'admin': return "Access Denied", 403
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.sku = request.form['sku']
        product.category = request.form['category']
        product.cost_price = float(request.form.get('cost_price', 0))
        product.selling_price = float(request.form.get('selling_price', 0))
        product.description = request.form['description']
        
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                delete_image(product.image_url)
                fname = secure_filename(file.filename)
                new_img = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + fname
                os.makedirs(os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER']), exist_ok=True)
                file.save(os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], new_img))
                product.image_url = new_img
                
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('edit_product.html', product=product, categories=Category.query.all())

@products_bp.route('/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    if current_user.role != 'admin': return "Access Denied", 403
    product = Product.query.get_or_404(product_id)
    delete_image(product.image_url)
    Transaction.query.filter_by(sku=product.sku).delete()
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('main.index'))

@products_bp.route('/product/<int:product_id>')
@login_required
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    history = Transaction.query.filter_by(sku=product.sku).order_by(Transaction.timestamp.desc()).all()
    return render_template('product_detail.html', product=product, history=history)

@products_bp.route('/export')
@login_required
def export_data():
    products = Product.query.all()
    data = [{'SKU': p.sku, 
            'Name': p.name, 
            'Category': p.category, 
            'Cost': p.cost_price, 
            'Price': p.selling_price,
            'Qty': p.current_quantity
        } for p in products]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: 
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, download_name="stock.xlsx", as_attachment=True)

@products_bp.route('/import', methods=['POST'])
@login_required
def import_data():
    if 'file' not in request.files: return redirect(url_for('main.index'))
    file = request.files['file']
    if file:
        try:
            df = pd.read_excel(file)
            for _, row in df.iterrows():
                sku = str(row['SKU'])
                product = Product.query.filter_by(sku=sku).first()
                if not product:
                    db.session.add(Product(sku=sku, name=row['Name'], category=row.get('Category','General'), cost_price=row.get('Cost', 0),
                    selling_price=row.get('Price', 0), current_quantity=row.get('Qty',0)))
            db.session.commit()
        except Exception as e: 
            print(f"Error importing: {e}")
    return redirect(url_for('main.index'))

@products_bp.route('/bulk_upload_images', methods=['POST'])
@login_required
def bulk_upload_images():
    if current_user.role != 'admin': return "Access Denied", 403
    
    if 'images' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('main.index'))
    
    files = request.files.getlist('images')
    updated_count = 0
    not_found_list = []

    for file in files:
        if file and allowed_file(file.filename):
            # ดึงชื่อไฟล์มาเป็น SKU (ตัดนามสกุลออก)
            filename = secure_filename(file.filename)
            sku_match = os.path.splitext(filename)[0]
            
            # ค้นหาสินค้าจาก SKU
            product = Product.query.filter_by(sku=sku_match).first()
            
            if product:
                # ลบรูปเก่า (ถ้ามี)
                delete_image(product.image_url)
                
                # ตั้งชื่อไฟล์ใหม่
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                new_filename = f"{timestamp}_{filename}"
                
                # บันทึกไฟล์
                os.makedirs(os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER']), exist_ok=True)
                file.save(os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], new_filename))
                
                # อัปเดตฐานข้อมูล
                product.image_url = new_filename
                updated_count += 1
            else:
                not_found_list.append(sku_match)

    db.session.commit()
    
    if updated_count > 0:
        flash(f'✅ Successfully updated images for {updated_count} products!', 'success')
    
    if not_found_list:
        flash(f'⚠️ SKU not found for images: {", ".join(not_found_list)}', 'warning')
        
    return redirect(url_for('main.index'))