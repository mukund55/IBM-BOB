"""
Enterprise Data Quality Platform - Authentication API
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import uuid

from models.models import db, User, AuditLog, Session as UserSession

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Please provide both username and password.', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user is None:
            flash('Invalid username or password.', 'danger')
            log_audit('login_failed', 'user', username, request.remote_addr)
            return render_template('auth/login.html')
        
        # Check if account is locked
        if user.is_locked():
            flash('Account is locked. Please try again later.', 'danger')
            return render_template('auth/login.html')
        
        # Check password
        if not user.check_password(password):
            user.failed_login_attempts += 1
            
            # Lock account after max attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                flash('Account locked due to multiple failed login attempts.', 'danger')
            else:
                flash('Invalid username or password.', 'danger')
            
            db.session.commit()
            log_audit('login_failed', 'user', username, request.remote_addr)
            return render_template('auth/login.html')
        
        # Check if user is active
        if not user.is_active:
            flash('Account is disabled. Please contact administrator.', 'danger')
            return render_template('auth/login.html')
        
        # Successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=remember)
        
        # Create session record
        create_user_session(user.id, request.remote_addr, request.user_agent.string)
        
        # Log audit
        log_audit('login_success', 'user', user.username, request.remote_addr, user.id)
        
        flash(f'Welcome back, {user.full_name or user.username}!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout handler"""
    username = current_user.username
    user_id = current_user.id
    
    # Deactivate session
    deactivate_user_session(user_id)
    
    # Log audit
    log_audit('logout', 'user', username, request.remote_addr, user_id)
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration (if enabled)"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('auth/register.html')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')
        
        # Create user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            role='analyst',  # Default role
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log audit
        log_audit('user_registered', 'user', username, request.remote_addr)
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash('All fields are required.', 'danger')
            return render_template('auth/change_password.html')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('auth/change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        # Log audit
        log_audit('password_changed', 'user', current_user.username, 
                 request.remote_addr, current_user.id)
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('auth/change_password.html')


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        
        # Check if email is already used by another user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Email already in use.', 'danger')
            return render_template('auth/profile.html')
        
        # Update profile
        current_user.full_name = full_name
        current_user.email = email
        db.session.commit()
        
        # Log audit
        log_audit('profile_updated', 'user', current_user.username,
                 request.remote_addr, current_user.id)
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html')


# API Endpoints
@auth_bp.route('/api/check-session', methods=['GET'])
@login_required
def check_session():
    """Check if session is valid"""
    return jsonify({
        'valid': True,
        'user': current_user.to_dict()
    })


@auth_bp.route('/api/user-info', methods=['GET'])
@login_required
def user_info():
    """Get current user information"""
    return jsonify(current_user.to_dict())


# Helper Functions
def log_audit(action, entity_type, entity_id, ip_address, user_id=None):
    """Log audit entry"""
    try:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=request.user_agent.string if request else None
        )
        db.session.add(audit)
        db.session.commit()
    except Exception as e:
        print(f"Error logging audit: {e}")


def create_user_session(user_id, ip_address, user_agent):
    """Create user session record"""
    try:
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        user_session = UserSession(
            session_id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            is_active=True
        )
        db.session.add(user_session)
        db.session.commit()
        
        session['session_id'] = session_id
    except Exception as e:
        print(f"Error creating session: {e}")


def deactivate_user_session(user_id):
    """Deactivate user session"""
    try:
        session_id = session.get('session_id')
        if session_id:
            user_session = UserSession.query.filter_by(
                session_id=session_id,
                user_id=user_id
            ).first()
            if user_session:
                user_session.is_active = False
                db.session.commit()
    except Exception as e:
        print(f"Error deactivating session: {e}")

# Made with Bob
