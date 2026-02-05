from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User   
from extensions import db

auth_bp = Blueprint('auth', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403) # ถ้าไม่ใช่ Admin ให้ขึ้นจอขาว Error 403
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/admin/users', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_users():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('ชื่อผู้ใช้นี้มีแล้ว', 'error')
        else:
            hashed_pw = generate_password_hash('1234')
            new_user = User(username=username, password=hashed_pw, role=role)
            db.session.add(new_user)
            db.session.commit()
            flash(f'เพิ่ม {username} สำเร็จ', 'success')
        return redirect(url_for('auth.manage_users')) # ระวังตรง auth.manage_users ต้องตรงกับชื่อ Blueprint

    users = User.query.all()
    return render_template('admin_users.html', users=users)

@auth_bp.route('/admin/users/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('ลบตัวเองไม่ได้', 'error')
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f'ลบ {user.username} แล้ว', 'success')
    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/admin/users/reset/<int:user_id>')
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    user.password = generate_password_hash('1234', method='sha256')
    db.session.commit()
    flash(f'รีเซ็ตรหัส {user.username} เป็น 1234 แล้ว', 'warning')
    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            return render_template('login.html', error="Invalid Username or Password")
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))