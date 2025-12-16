"""
Customer Data Management Application (CRM)

Demonstrates:
- Flask web framework with sessions
- User authentication with password hashing
- Role-based access control
- CRUD operations via REST API
- Data validation
- Pagination
- Audit logging
- CSV Export
"""

from flask import Flask, render_template, request, jsonify, Response, session, redirect, url_for
from functools import wraps
import re
import csv
import io
from database import (
    init_db, 
    create_customer, get_all_customers, get_customer_by_id, 
    update_customer, delete_customer, search_customers,
    get_customers_paginated, get_customer_count,
    create_policy, get_policies_by_customer, get_all_policies,
    get_policy_by_id, update_policy, delete_policy,
    get_dashboard_stats,
    create_user, authenticate_user, get_user_by_id, get_all_users,
    update_user_role, delete_user,
    log_action, get_audit_logs,
    # Claims and alerts
    create_claim, get_all_claims, get_claim_by_id, update_claim, delete_claim,
    get_claim_types, get_claims_stats, get_renewal_alerts, get_expiring_policies,
    # Analytics
    get_policy_breakdown, get_revenue_by_month, get_claims_by_status,
    get_claims_by_type, get_customer_lifetime_value, get_monthly_report_data
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production-123!'  # Change this in production!

# Initialize database on startup
init_db()


# ============================================
# AUTHENTICATION DECORATORS
# ============================================

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get current logged-in user info"""
    if 'user_id' in session:
        return {
            'id': session['user_id'],
            'username': session['username'],
            'role': session['role']
        }
    return None


# ============================================
# DATA VALIDATION
# ============================================

def validate_customer_data(data):
    """Validate customer input data"""
    errors = []
    
    if not data.get('name') or not data['name'].strip():
        errors.append("Name is required")
    
    if not data.get('email') or not data['email'].strip():
        errors.append("Email is required")
    else:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            errors.append("Invalid email format")
    
    if data.get('phone') and data['phone'].strip():
        phone_pattern = r'^[\d\s\-\+\(\)]{7,20}$'
        if not re.match(phone_pattern, data['phone']):
            errors.append("Invalid phone format")
    
    if errors:
        return False, errors
    return True, None


def validate_policy_data(data):
    """Validate policy input data"""
    errors = []
    
    if not data.get('customer_id'):
        errors.append("Customer is required")
    
    if not data.get('policy_type'):
        errors.append("Policy type is required")
    
    if not data.get('policy_number') or not data['policy_number'].strip():
        errors.append("Policy number is required")
    
    if not data.get('premium') or float(data.get('premium', 0)) <= 0:
        errors.append("Premium must be greater than 0")
    
    if not data.get('start_date'):
        errors.append("Start date is required")
    
    if not data.get('end_date'):
        errors.append("End date is required")
    
    if errors:
        return False, errors
    return True, None


# ============================================
# AUTH ROUTES
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('index'))
        return render_template('login.html')
    
    # POST - handle login
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    user = authenticate_user(username, password)
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        
        log_action(user['id'], user['username'], 'login', 'user', user['id'], 
                   {'action': 'User logged in'}, request.remote_addr)
        
        return jsonify({'success': True, 'user': {'username': user['username'], 'role': user['role']}})
    
    return jsonify({'success': False, 'error': 'Invalid username or password'}), 401


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('index'))
        return render_template('login.html', register=True)
    
    # POST - handle registration
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({'success': False, 'error': 'Invalid email format'}), 400
    
    try:
        user_id = create_user(username, email, password, role='agent')
        
        log_action(user_id, username, 'register', 'user', user_id,
                   {'action': 'New user registered'}, request.remote_addr)
        
        return jsonify({'success': True, 'message': 'Registration successful! Please login.'})
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'success': False, 'error': 'Username or email already exists'}), 400
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/logout')
def logout():
    """Logout user"""
    if 'user_id' in session:
        log_action(session['user_id'], session['username'], 'logout', 'user', session['user_id'],
                   {'action': 'User logged out'}, request.remote_addr)
    session.clear()
    return redirect(url_for('login'))


@app.route('/api/me')
@login_required
def api_me():
    """Get current user info"""
    return jsonify(get_current_user())


# ============================================
# MAIN ROUTES
# ============================================

@app.route('/')
@login_required
def index():
    """Main page - display all customers"""
    return render_template('index.html', user=get_current_user())


# ============================================
# CUSTOMER API
# ============================================

@app.route('/api/customers', methods=['GET'])
@login_required
def api_get_customers():
    """API: Get customers with pagination and search"""
    query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    per_page = min(per_page, 100)
    
    customers = get_customers_paginated(page, per_page, query)
    total = get_customer_count(query)
    total_pages = (total + per_page - 1) // per_page
    
    return jsonify({
        'customers': customers,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    })


@app.route('/api/customers', methods=['POST'])
@login_required
def api_create_customer():
    """API: Create a new customer"""
    data = request.get_json()
    
    is_valid, errors = validate_customer_data(data)
    if not is_valid:
        return jsonify({'success': False, 'errors': errors}), 400
    
    try:
        customer_id = create_customer(
            name=data['name'].strip(),
            email=data['email'].strip(),
            phone=data.get('phone', '').strip(),
            address=data.get('address', '').strip()
        )
        
        log_action(session['user_id'], session['username'], 'create', 'customer', customer_id,
                   {'name': data['name'], 'email': data['email']}, request.remote_addr)
        
        return jsonify({'success': True, 'id': customer_id})
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'success': False, 'errors': ['Email already exists']}), 400
        return jsonify({'success': False, 'errors': [str(e)]}), 500


@app.route('/api/customers/<int:customer_id>', methods=['GET'])
@login_required
def api_get_customer(customer_id):
    """API: Get a single customer"""
    customer = get_customer_by_id(customer_id)
    if customer:
        return jsonify(customer)
    return jsonify({'error': 'Customer not found'}), 404


@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
@login_required
def api_update_customer(customer_id):
    """API: Update a customer"""
    data = request.get_json()
    
    is_valid, errors = validate_customer_data(data)
    if not is_valid:
        return jsonify({'success': False, 'errors': errors}), 400
    
    # Get old data for audit log
    old_customer = get_customer_by_id(customer_id)
    
    try:
        success = update_customer(
            customer_id=customer_id,
            name=data['name'].strip(),
            email=data['email'].strip(),
            phone=data.get('phone', '').strip(),
            address=data.get('address', '').strip()
        )
        if success:
            log_action(session['user_id'], session['username'], 'update', 'customer', customer_id,
                       {'old': old_customer, 'new': data}, request.remote_addr)
            return jsonify({'success': True})
        return jsonify({'success': False, 'errors': ['Customer not found']}), 404
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'success': False, 'errors': ['Email already exists']}), 400
        return jsonify({'success': False, 'errors': [str(e)]}), 500


@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
@admin_required  # Only admins can delete
def api_delete_customer(customer_id):
    """API: Delete a customer (Admin only)"""
    old_customer = get_customer_by_id(customer_id)
    
    success = delete_customer(customer_id)
    if success:
        log_action(session['user_id'], session['username'], 'delete', 'customer', customer_id,
                   {'deleted': old_customer}, request.remote_addr)
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': ['Customer not found']}), 404


# ============================================
# POLICY API
# ============================================

@app.route('/api/policies', methods=['GET'])
@login_required
def api_get_policies():
    """API: Get all policies"""
    customer_id = request.args.get('customer_id', type=int)
    
    if customer_id:
        policies = get_policies_by_customer(customer_id)
    else:
        policies = get_all_policies()
    
    return jsonify(policies)


@app.route('/api/policies', methods=['POST'])
@login_required
def api_create_policy():
    """API: Create a new policy"""
    data = request.get_json()
    
    is_valid, errors = validate_policy_data(data)
    if not is_valid:
        return jsonify({'success': False, 'errors': errors}), 400
    
    try:
        policy_id = create_policy(
            customer_id=data['customer_id'],
            policy_type=data['policy_type'],
            policy_number=data['policy_number'].strip(),
            premium=float(data['premium']),
            start_date=data['start_date'],
            end_date=data['end_date'],
            status=data.get('status', 'active')
        )
        
        log_action(session['user_id'], session['username'], 'create', 'policy', policy_id,
                   {'policy_number': data['policy_number'], 'customer_id': data['customer_id']}, request.remote_addr)
        
        return jsonify({'success': True, 'id': policy_id})
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'success': False, 'errors': ['Policy number already exists']}), 400
        return jsonify({'success': False, 'errors': [str(e)]}), 500


@app.route('/api/policies/<int:policy_id>', methods=['GET'])
@login_required
def api_get_policy(policy_id):
    """API: Get a single policy"""
    policy = get_policy_by_id(policy_id)
    if policy:
        return jsonify(policy)
    return jsonify({'error': 'Policy not found'}), 404


@app.route('/api/policies/<int:policy_id>', methods=['PUT'])
@login_required
def api_update_policy(policy_id):
    """API: Update a policy"""
    data = request.get_json()
    
    is_valid, errors = validate_policy_data(data)
    if not is_valid:
        return jsonify({'success': False, 'errors': errors}), 400
    
    old_policy = get_policy_by_id(policy_id)
    
    try:
        success = update_policy(
            policy_id=policy_id,
            policy_type=data['policy_type'],
            policy_number=data['policy_number'].strip(),
            premium=float(data['premium']),
            start_date=data['start_date'],
            end_date=data['end_date'],
            status=data.get('status', 'active')
        )
        if success:
            log_action(session['user_id'], session['username'], 'update', 'policy', policy_id,
                       {'old': old_policy, 'new': data}, request.remote_addr)
            return jsonify({'success': True})
        return jsonify({'success': False, 'errors': ['Policy not found']}), 404
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'success': False, 'errors': ['Policy number already exists']}), 400
        return jsonify({'success': False, 'errors': [str(e)]}), 500


@app.route('/api/policies/<int:policy_id>', methods=['DELETE'])
@admin_required  # Only admins can delete
def api_delete_policy(policy_id):
    """API: Delete a policy (Admin only)"""
    old_policy = get_policy_by_id(policy_id)
    
    success = delete_policy(policy_id)
    if success:
        log_action(session['user_id'], session['username'], 'delete', 'policy', policy_id,
                   {'deleted': old_policy}, request.remote_addr)
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': ['Policy not found']}), 404


# ============================================
# DASHBOARD & STATS API
# ============================================

@app.route('/api/stats', methods=['GET'])
@login_required
def api_get_stats():
    """API: Get dashboard statistics"""
    stats = get_dashboard_stats()
    return jsonify(stats)


# ============================================
# AUDIT LOG API (Admin only)
# ============================================

@app.route('/api/audit-logs', methods=['GET'])
@admin_required
def api_get_audit_logs():
    """API: Get audit logs (Admin only)"""
    limit = request.args.get('limit', 100, type=int)
    entity_type = request.args.get('entity_type')
    
    logs = get_audit_logs(limit, entity_type)
    return jsonify(logs)


# ============================================
# USER MANAGEMENT API (Admin only)
# ============================================

@app.route('/api/users', methods=['GET'])
@admin_required
def api_get_users():
    """API: Get all users (Admin only)"""
    users = get_all_users()
    return jsonify(users)


@app.route('/api/users/<int:user_id>/role', methods=['PUT'])
@admin_required
def api_update_user_role(user_id):
    """API: Update user role (Admin only)"""
    data = request.get_json()
    new_role = data.get('role')
    
    if new_role not in ['admin', 'agent']:
        return jsonify({'success': False, 'error': 'Invalid role'}), 400
    
    # Prevent removing last admin
    if new_role == 'agent':
        users = get_all_users()
        admin_count = sum(1 for u in users if u['role'] == 'admin')
        target_user = next((u for u in users if u['id'] == user_id), None)
        if target_user and target_user['role'] == 'admin' and admin_count <= 1:
            return jsonify({'success': False, 'error': 'Cannot remove the last admin'}), 400
    
    success = update_user_role(user_id, new_role)
    if success:
        log_action(session['user_id'], session['username'], 'update', 'user', user_id,
                   {'role_changed_to': new_role}, request.remote_addr)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'User not found'}), 404


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def api_delete_user(user_id):
    """API: Delete a user (Admin only)"""
    # Prevent self-deletion
    if user_id == session['user_id']:
        return jsonify({'success': False, 'error': 'Cannot delete yourself'}), 400
    
    # Prevent deleting last admin
    users = get_all_users()
    target_user = next((u for u in users if u['id'] == user_id), None)
    if target_user and target_user['role'] == 'admin':
        admin_count = sum(1 for u in users if u['role'] == 'admin')
        if admin_count <= 1:
            return jsonify({'success': False, 'error': 'Cannot delete the last admin'}), 400
    
    success = delete_user(user_id)
    if success:
        log_action(session['user_id'], session['username'], 'delete', 'user', user_id,
                   {'deleted_user': target_user['username'] if target_user else None}, request.remote_addr)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'User not found'}), 404


# ============================================
# CSV EXPORT
# ============================================

@app.route('/api/export/customers', methods=['GET'])
@login_required
def api_export_customers():
    """API: Export all customers as CSV"""
    customers = get_all_customers()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Address', 'Created At'])
    
    for customer in customers:
        writer.writerow([
            customer['id'],
            customer['name'],
            customer['email'],
            customer['phone'] or '',
            customer['address'] or '',
            customer['created_at']
        ])
    
    log_action(session['user_id'], session['username'], 'export', 'customer', None,
               {'count': len(customers)}, request.remote_addr)
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=customers_export.csv'}
    )


@app.route('/api/export/policies', methods=['GET'])
@login_required
def api_export_policies():
    """API: Export all policies as CSV"""
    policies = get_all_policies()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Customer', 'Email', 'Policy Type', 'Policy Number', 'Premium', 'Start Date', 'End Date', 'Status'])
    
    for policy in policies:
        writer.writerow([
            policy['id'],
            policy['customer_name'],
            policy['customer_email'],
            policy['policy_type'],
            policy['policy_number'],
            policy['premium'],
            policy['start_date'],
            policy['end_date'],
            policy['status']
        ])
    
    log_action(session['user_id'], session['username'], 'export', 'policy', None,
               {'count': len(policies)}, request.remote_addr)
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=policies_export.csv'}
    )


# ============================================
# CLAIMS API
# ============================================

@app.route('/api/claims', methods=['GET'])
@login_required
def api_get_claims():
    """API: Get all claims"""
    claims = get_all_claims()
    return jsonify(claims)


@app.route('/api/claims', methods=['POST'])
@login_required
def api_create_claim():
    """API: Create a new claim"""
    data = request.get_json()
    
    # Validate required fields
    errors = []
    if not data.get('policy_id'):
        errors.append('Policy is required')
    if not data.get('claim_number'):
        errors.append('Claim number is required')
    if not data.get('claim_type'):
        errors.append('Claim type is required')
    if not data.get('filed_date'):
        errors.append('Filed date is required')
    
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400
    
    try:
        claim_id = create_claim(
            policy_id=data['policy_id'],
            claim_number=data['claim_number'].strip(),
            claim_type=data['claim_type'],
            description=data.get('description', '').strip(),
            amount=float(data.get('amount', 0)),
            filed_date=data['filed_date'],
            status=data.get('status', 'submitted')
        )
        
        log_action(session['user_id'], session['username'], 'create', 'claim', claim_id,
                   {'claim_number': data['claim_number']}, request.remote_addr)
        
        return jsonify({'success': True, 'id': claim_id})
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'success': False, 'errors': ['Claim number already exists']}), 400
        return jsonify({'success': False, 'errors': [str(e)]}), 500


@app.route('/api/claims/<int:claim_id>', methods=['GET'])
@login_required
def api_get_claim(claim_id):
    """API: Get a single claim"""
    claim = get_claim_by_id(claim_id)
    if claim:
        return jsonify(claim)
    return jsonify({'error': 'Claim not found'}), 404


@app.route('/api/claims/<int:claim_id>', methods=['PUT'])
@login_required
def api_update_claim(claim_id):
    """API: Update a claim"""
    data = request.get_json()
    
    old_claim = get_claim_by_id(claim_id)
    
    try:
        success = update_claim(
            claim_id=claim_id,
            claim_type=data['claim_type'],
            description=data.get('description', '').strip(),
            amount=float(data.get('amount', 0)),
            status=data.get('status', 'submitted'),
            resolved_date=data.get('resolved_date')
        )
        if success:
            log_action(session['user_id'], session['username'], 'update', 'claim', claim_id,
                       {'old_status': old_claim.get('status'), 'new_status': data.get('status')}, request.remote_addr)
            return jsonify({'success': True})
        return jsonify({'success': False, 'errors': ['Claim not found']}), 404
    except Exception as e:
        return jsonify({'success': False, 'errors': [str(e)]}), 500


@app.route('/api/claims/<int:claim_id>', methods=['DELETE'])
@admin_required
def api_delete_claim(claim_id):
    """API: Delete a claim (Admin only)"""
    old_claim = get_claim_by_id(claim_id)
    
    success = delete_claim(claim_id)
    if success:
        log_action(session['user_id'], session['username'], 'delete', 'claim', claim_id,
                   {'deleted': old_claim}, request.remote_addr)
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': ['Claim not found']}), 404


@app.route('/api/claim-types', methods=['GET'])
@login_required
def api_get_claim_types():
    """API: Get available claim types by policy type"""
    return jsonify(get_claim_types())


# ============================================
# RENEWAL ALERTS API
# ============================================

@app.route('/api/renewal-alerts', methods=['GET'])
@login_required
def api_get_renewal_alerts():
    """API: Get policies expiring soon, grouped by urgency"""
    alerts = get_renewal_alerts()
    return jsonify(alerts)


@app.route('/api/stats/claims', methods=['GET'])
@login_required
def api_get_claims_stats():
    """API: Get claims statistics"""
    stats = get_claims_stats()
    return jsonify(stats)


@app.route('/api/send-reminder/<int:policy_id>', methods=['POST'])
@admin_required
def api_send_manual_reminder(policy_id):
    """API: Manually send a renewal reminder (Admin only)"""
    from email_service import send_renewal_reminder
    from database import get_policy_by_id, get_customer_by_id
    from datetime import datetime
    
    policy = get_policy_by_id(policy_id)
    if not policy:
        return jsonify({'success': False, 'error': 'Policy not found'}), 404
    
    customer = get_customer_by_id(policy['customer_id'])
    if not customer:
        return jsonify({'success': False, 'error': 'Customer not found'}), 404
    
    # Combine policy and customer info
    policy_info = {**policy, 'customer_name': customer['name'], 'customer_email': customer['email']}
    
    # Calculate days until expiry
    end_date = datetime.strptime(policy['end_date'], '%Y-%m-%d')
    days_until = (end_date - datetime.now()).days
    
    success = send_renewal_reminder(policy_info, max(1, days_until))
    
    if success:
        log_action(session['user_id'], session['username'], 'send_reminder', 'policy', policy_id,
                   {'sent_to': customer['email']}, request.remote_addr)
        return jsonify({'success': True, 'message': f'Reminder sent to {customer["email"]}'})
    
    return jsonify({'success': False, 'error': 'Failed to send reminder'}), 500


# ============================================
# ANALYTICS API
# ============================================

@app.route('/api/analytics/policies', methods=['GET'])
@login_required
def api_analytics_policies():
    """API: Get policy breakdown by type"""
    return jsonify(get_policy_breakdown())


@app.route('/api/analytics/revenue', methods=['GET'])
@login_required
def api_analytics_revenue():
    """API: Get monthly revenue data"""
    months = request.args.get('months', 6, type=int)
    return jsonify(get_revenue_by_month(months))


@app.route('/api/analytics/claims-status', methods=['GET'])
@login_required
def api_analytics_claims_status():
    """API: Get claims by status"""
    return jsonify(get_claims_by_status())


@app.route('/api/analytics/claims-type', methods=['GET'])
@login_required
def api_analytics_claims_type():
    """API: Get claims by type"""
    return jsonify(get_claims_by_type())


@app.route('/api/analytics/clv', methods=['GET'])
@login_required
def api_analytics_clv():
    """API: Get customer lifetime value"""
    return jsonify(get_customer_lifetime_value())


@app.route('/api/reports/monthly', methods=['GET'])
@admin_required
def api_monthly_report():
    """API: Generate monthly PDF report (Admin only)"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from datetime import datetime
    
    data = get_monthly_report_data()
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=30, textColor=colors.HexColor('#1a1a2e'))
    story.append(Paragraph(f"Insurance CRM - Monthly Report", title_style))
    story.append(Paragraph(f"{data['month']}", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Summary Stats
    story.append(Paragraph("Summary Statistics", styles['Heading2']))
    summary_data = [
        ['Metric', 'Value'],
        ['New Customers', str(data['new_customers'])],
        ['New Policies', str(data['new_policies'])],
        ['New Premium', f"${data['new_premium']:,.2f}"],
        ['Claims Filed', str(data['claims_filed'])],
        ['Claims Amount', f"${data['claims_amount']:,.2f}"],
        ['Expiring Policies', str(data['expiring_policies'])],
    ]
    summary_table = Table(summary_data, colWidths=[200, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # Policy Breakdown
    if data['policy_breakdown']:
        story.append(Paragraph("Policies by Type", styles['Heading2']))
        policy_data = [['Type', 'Count', 'Total Premium']]
        for p in data['policy_breakdown']:
            policy_data.append([p['policy_type'].title(), str(p['count']), f"${p['total_premium']:,.2f}"])
        policy_table = Table(policy_data, colWidths=[150, 100, 150])
        policy_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        story.append(policy_table)
        story.append(Spacer(1, 30))
    
    # Top Customers
    if data['top_customers']:
        story.append(Paragraph("Top Customers by Lifetime Value", styles['Heading2']))
        clv_data = [['Customer', 'Policies', 'Total Premium']]
        for c in data['top_customers'][:5]:
            clv_data.append([c['name'], str(c['policy_count']), f"${c['total_premium']:,.2f}"])
        clv_table = Table(clv_data, colWidths=[200, 80, 120])
        clv_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        story.append(clv_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    log_action(session['user_id'], session['username'], 'generate_report', 'report', None,
               {'type': 'monthly', 'month': data['month']}, request.remote_addr)
    
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=monthly_report_{datetime.now().strftime("%Y%m")}.pdf'}
    )


# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  Insurance CRM System")
    print("  Open: http://127.0.0.1:5000")
    print("  Default login: admin / admin123")
    print("="*50 + "\n")
    
    # Start background scheduler for email reminders
    try:
        from email_service import start_scheduler
        scheduler = start_scheduler()
    except Exception as e:
        print(f"Note: Email scheduler not started: {e}")
    
    app.run(debug=True)
