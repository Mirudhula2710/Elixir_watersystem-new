from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash(f"Please log in with a {role.capitalize()} account to access that page.")
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session['role'] = user.role
            if user.role == 'manager':
                return redirect(url_for('manager_dashboard')) # to be implemented
            elif user.role == 'worker':
                return redirect(url_for('worker_dashboard')) # to be implemented
            elif user.role == 'student':
                return redirect(url_for('student_dashboard')) # to be implemented
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('role', None)
    return redirect(url_for('auth.login'))
