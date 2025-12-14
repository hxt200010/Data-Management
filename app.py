"""
Customer Data Management Application (CRM)

Demonstrates:
- Flask web framework
- CRUD operations via REST API
- Data validation
- Search functionality
- Pagination
- Policy management
- Dashboard statistics
- CSV Export
"""

from flask import Flask, render_template, request, jsonify, Response
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
    get_dashboard_stats
)

app = Flask(__name__)

# Initialize database on startup
init_db()


# ============================================
# DATA VALIDATION
# ============================================

def validate_customer_data(data):
    """
    Validate customer input data
    Returns: (is_valid, error_message)
    """
    errors = []
    
    # Check required fields
    if not data.get('name') or not data['name'].strip():
        errors.append("Name is required")
    
    if not data.get('email') or not data['email'].strip():
        errors.append("Email is required")
    else:
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            errors.append("Invalid email format")
    
    # Validate phone format (optional but must be valid if provided)
    if data.get('phone') and data['phone'].strip():
        phone_pattern = r'^[\d\s\-\+\(\)]{7,20}$'
        if not re.match(phone_pattern, data['phone']):
            errors.append("Invalid phone format (use digits, spaces, or dashes)")
    
    if errors:
        return False, errors
    return True, None


def validate_policy_data(data):
    """
    Validate policy input data
    Returns: (is_valid, error_message)
    """
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
# ROUTES
# ============================================

@app.route('/')
def index():
    """Main page - display all customers"""
    customers = get_all_customers()
    return render_template('index.html', customers=customers)


# ============================================
# CUSTOMER API
# ============================================

@app.route('/api/customers', methods=['GET'])
def api_get_customers():
    """API: Get customers with pagination and search"""
    query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Limit per_page to prevent abuse
    per_page = min(per_page, 100)
    
    customers = get_customers_paginated(page, per_page, query)
    total = get_customer_count(query)
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
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
def api_create_customer():
    """API: Create a new customer"""
    data = request.get_json()
    
    # Validate data
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
        return jsonify({'success': True, 'id': customer_id})
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'success': False, 'errors': ['Email already exists']}), 400
        return jsonify({'success': False, 'errors': [str(e)]}), 500


@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def api_get_customer(customer_id):
    """API: Get a single customer"""
    customer = get_customer_by_id(customer_id)
    if customer:
        return jsonify(customer)
    return jsonify({'error': 'Customer not found'}), 404


@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def api_update_customer(customer_id):
    """API: Update a customer"""
    data = request.get_json()
    
    # Validate data
    is_valid, errors = validate_customer_data(data)
    if not is_valid:
        return jsonify({'success': False, 'errors': errors}), 400
    
    try:
        success = update_customer(
            customer_id=customer_id,
            name=data['name'].strip(),
            email=data['email'].strip(),
            phone=data.get('phone', '').strip(),
            address=data.get('address', '').strip()
        )
        if success:
            return jsonify({'success': True})
        return jsonify({'success': False, 'errors': ['Customer not found']}), 404
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'success': False, 'errors': ['Email already exists']}), 400
        return jsonify({'success': False, 'errors': [str(e)]}), 500


@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def api_delete_customer(customer_id):
    """API: Delete a customer"""
    success = delete_customer(customer_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': ['Customer not found']}), 404


# ============================================
# POLICY API
# ============================================

@app.route('/api/policies', methods=['GET'])
def api_get_policies():
    """API: Get all policies"""
    customer_id = request.args.get('customer_id', type=int)
    
    if customer_id:
        policies = get_policies_by_customer(customer_id)
    else:
        policies = get_all_policies()
    
    return jsonify(policies)


@app.route('/api/policies', methods=['POST'])
def api_create_policy():
    """API: Create a new policy"""
    data = request.get_json()
    
    # Validate data
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
        return jsonify({'success': True, 'id': policy_id})
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'success': False, 'errors': ['Policy number already exists']}), 400
        return jsonify({'success': False, 'errors': [str(e)]}), 500


@app.route('/api/policies/<int:policy_id>', methods=['GET'])
def api_get_policy(policy_id):
    """API: Get a single policy"""
    policy = get_policy_by_id(policy_id)
    if policy:
        return jsonify(policy)
    return jsonify({'error': 'Policy not found'}), 404


@app.route('/api/policies/<int:policy_id>', methods=['PUT'])
def api_update_policy(policy_id):
    """API: Update a policy"""
    data = request.get_json()
    
    # Validate data
    is_valid, errors = validate_policy_data(data)
    if not is_valid:
        return jsonify({'success': False, 'errors': errors}), 400
    
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
            return jsonify({'success': True})
        return jsonify({'success': False, 'errors': ['Policy not found']}), 404
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'success': False, 'errors': ['Policy number already exists']}), 400
        return jsonify({'success': False, 'errors': [str(e)]}), 500


@app.route('/api/policies/<int:policy_id>', methods=['DELETE'])
def api_delete_policy(policy_id):
    """API: Delete a policy"""
    success = delete_policy(policy_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': ['Policy not found']}), 404


# ============================================
# DASHBOARD API
# ============================================

@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    """API: Get dashboard statistics"""
    stats = get_dashboard_stats()
    return jsonify(stats)


# ============================================
# CSV EXPORT
# ============================================

@app.route('/api/export/customers', methods=['GET'])
def api_export_customers():
    """API: Export all customers as CSV"""
    customers = get_all_customers()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Address', 'Created At'])
    
    # Data rows
    for customer in customers:
        writer.writerow([
            customer['id'],
            customer['name'],
            customer['email'],
            customer['phone'] or '',
            customer['address'] or '',
            customer['created_at']
        ])
    
    # Create response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=customers_export.csv'}
    )


@app.route('/api/export/policies', methods=['GET'])
def api_export_policies():
    """API: Export all policies as CSV"""
    policies = get_all_policies()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'Customer', 'Email', 'Policy Type', 'Policy Number', 'Premium', 'Start Date', 'End Date', 'Status'])
    
    # Data rows
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
    
    # Create response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=policies_export.csv'}
    )


# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  Insurance CRM System")
    print("  Open: http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(debug=True)
