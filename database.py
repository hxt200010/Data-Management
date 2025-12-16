"""
Database Module - SQLite Setup & Operations

Demonstrates:
- SQLite database connection
- Table creation with SQL
- CRUD helper functions
- Pagination
- Policy management
- Dashboard statistics
- User authentication with password hashing
- Audit logging
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# Database file path
DATABASE = os.path.join(os.path.dirname(__file__), 'customers.db')


def get_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_db():
    """Initialize the database and create tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create policies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            policy_type TEXT NOT NULL,
            policy_number TEXT UNIQUE NOT NULL,
            premium REAL NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
        )
    ''')
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'agent',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create audit log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create claims table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_id INTEGER NOT NULL,
            claim_number TEXT UNIQUE NOT NULL,
            claim_type TEXT NOT NULL,
            description TEXT,
            amount REAL,
            status TEXT DEFAULT 'submitted',
            filed_date DATE NOT NULL,
            resolved_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (policy_id) REFERENCES policies (id) ON DELETE CASCADE
        )
    ''')
    
    # Create notifications table for tracking sent reminders
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_id INTEGER NOT NULL,
            notification_type TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (policy_id) REFERENCES policies (id) ON DELETE CASCADE
        )
    ''')
    
    # Create default admin user if not exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_hash = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin@company.com', admin_hash, 'admin'))
        print("Default admin user created (admin / admin123)")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")


# ============================================
# USER AUTHENTICATION
# ============================================

def create_user(username, email, password, role='agent'):
    """Create a new user with hashed password"""
    conn = get_connection()
    cursor = conn.cursor()
    
    password_hash = generate_password_hash(password)
    
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    ''', (username, email, password_hash, role))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def authenticate_user(username, password):
    """Verify username and password, return user if valid"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        return dict(user)
    return None


def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, email, role, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    conn.close()
    return dict(user) if user else None


def get_all_users():
    """Get all users (for admin)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()
    
    conn.close()
    return [dict(row) for row in users]


def update_user_role(user_id, role):
    """Update user role"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE users SET role = ? WHERE id = ?', (role, user_id))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def delete_user(user_id):
    """Delete a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


# ============================================
# AUDIT LOGGING
# ============================================

def log_action(user_id, username, action, entity_type, entity_id=None, details=None, ip_address=None):
    """Log an action to the audit log"""
    conn = get_connection()
    cursor = conn.cursor()
    
    details_json = json.dumps(details) if details else None
    
    cursor.execute('''
        INSERT INTO audit_log (user_id, username, action, entity_type, entity_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, action, entity_type, entity_id, details_json, ip_address))
    
    conn.commit()
    conn.close()


def get_audit_logs(limit=100, entity_type=None):
    """Get audit logs with optional filtering"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if entity_type:
        cursor.execute('''
            SELECT * FROM audit_log
            WHERE entity_type = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (entity_type, limit))
    else:
        cursor.execute('''
            SELECT * FROM audit_log
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
    
    logs = cursor.fetchall()
    conn.close()
    return [dict(row) for row in logs]


# ============================================
# CUSTOMER CRUD OPERATIONS
# ============================================

def create_customer(name, email, phone, address):
    """Create a new customer record"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO customers (name, email, phone, address)
        VALUES (?, ?, ?, ?)
    ''', (name, email, phone, address))
    
    customer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return customer_id


def get_all_customers():
    """Read all customer records"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM customers ORDER BY created_at DESC')
    customers = cursor.fetchall()
    
    conn.close()
    return [dict(row) for row in customers]


def get_customer_by_id(customer_id):
    """Read a single customer by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
    customer = cursor.fetchone()
    
    conn.close()
    return dict(customer) if customer else None


def update_customer(customer_id, name, email, phone, address):
    """Update an existing customer record"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE customers
        SET name = ?, email = ?, phone = ?, address = ?
        WHERE id = ?
    ''', (name, email, phone, address, customer_id))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def delete_customer(customer_id):
    """Delete a customer record"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Delete associated policies first
    cursor.execute('DELETE FROM policies WHERE customer_id = ?', (customer_id,))
    cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def search_customers(query):
    """Search customers by name, email, or phone"""
    conn = get_connection()
    cursor = conn.cursor()
    
    search_term = f'%{query}%'
    cursor.execute('''
        SELECT * FROM customers
        WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
        ORDER BY created_at DESC
    ''', (search_term, search_term, search_term))
    
    customers = cursor.fetchall()
    conn.close()
    return [dict(row) for row in customers]


# ============================================
# PAGINATION
# ============================================

def get_customers_paginated(page=1, per_page=10, search=''):
    """Get customers with pagination and optional search"""
    conn = get_connection()
    cursor = conn.cursor()
    
    offset = (page - 1) * per_page
    
    if search:
        search_term = f'%{search}%'
        cursor.execute('''
            SELECT * FROM customers
            WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (search_term, search_term, search_term, per_page, offset))
    else:
        cursor.execute('''
            SELECT * FROM customers
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
    
    customers = cursor.fetchall()
    conn.close()
    return [dict(row) for row in customers]


def get_customer_count(search=''):
    """Get total count of customers (for pagination)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if search:
        search_term = f'%{search}%'
        cursor.execute('''
            SELECT COUNT(*) FROM customers
            WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
        ''', (search_term, search_term, search_term))
    else:
        cursor.execute('SELECT COUNT(*) FROM customers')
    
    count = cursor.fetchone()[0]
    conn.close()
    return count


# ============================================
# POLICY CRUD OPERATIONS
# ============================================

def create_policy(customer_id, policy_type, policy_number, premium, start_date, end_date, status='active'):
    """Create a new policy"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO policies (customer_id, policy_type, policy_number, premium, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (customer_id, policy_type, policy_number, premium, start_date, end_date, status))
    
    policy_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return policy_id


def get_policies_by_customer(customer_id):
    """Get all policies for a customer"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM policies
        WHERE customer_id = ?
        ORDER BY end_date ASC
    ''', (customer_id,))
    
    policies = cursor.fetchall()
    conn.close()
    return [dict(row) for row in policies]


def get_all_policies():
    """Get all policies with customer info"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.*, c.name as customer_name, c.email as customer_email
        FROM policies p
        JOIN customers c ON p.customer_id = c.id
        ORDER BY p.end_date ASC
    ''')
    
    policies = cursor.fetchall()
    conn.close()
    return [dict(row) for row in policies]


def get_policy_by_id(policy_id):
    """Get a single policy by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM policies WHERE id = ?', (policy_id,))
    policy = cursor.fetchone()
    
    conn.close()
    return dict(policy) if policy else None


def update_policy(policy_id, policy_type, policy_number, premium, start_date, end_date, status):
    """Update an existing policy"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE policies
        SET policy_type = ?, policy_number = ?, premium = ?, start_date = ?, end_date = ?, status = ?
        WHERE id = ?
    ''', (policy_type, policy_number, premium, start_date, end_date, status, policy_id))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def delete_policy(policy_id):
    """Delete a policy"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM policies WHERE id = ?', (policy_id,))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


# ============================================
# DASHBOARD STATS
# ============================================

def get_dashboard_stats():
    """Get statistics for dashboard"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total customers
    cursor.execute('SELECT COUNT(*) FROM customers')
    total_customers = cursor.fetchone()[0]
    
    # Total policies
    cursor.execute('SELECT COUNT(*) FROM policies')
    total_policies = cursor.fetchone()[0]
    
    # Active policies
    cursor.execute("SELECT COUNT(*) FROM policies WHERE status = 'active'")
    active_policies = cursor.fetchone()[0]
    
    # Policies expiring in 30 days
    thirty_days = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(*) FROM policies
        WHERE end_date BETWEEN ? AND ? AND status = 'active'
    ''', (today, thirty_days))
    expiring_soon = cursor.fetchone()[0]
    
    # Total premium
    cursor.execute("SELECT COALESCE(SUM(premium), 0) FROM policies WHERE status = 'active'")
    total_premium = cursor.fetchone()[0]
    
    # Total users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_customers': total_customers,
        'total_policies': total_policies,
        'active_policies': active_policies,
        'expiring_soon': expiring_soon,
        'total_premium': round(total_premium, 2),
        'total_users': total_users
    }


# ============================================
# CLAIMS CRUD OPERATIONS
# ============================================

# Comprehensive claim types for real insurance scenarios
CLAIM_TYPES = {
    'auto': [
        'collision',           # Vehicle collision with another car
        'comprehensive',       # Non-collision (theft, vandalism, weather)
        'liability',           # Damage to other party
        'uninsured_motorist',  # Hit by uninsured driver
        'medical_payment',     # Medical bills from accident
        'roadside_assistance', # Towing, lockout, etc.
        'rental_reimbursement', # Rental car while yours is repaired
        'glass_damage',        # Windshield/window damage
    ],
    'home': [
        'fire_damage',         # Fire or smoke damage
        'water_damage',        # Flooding, burst pipes, leaks
        'theft_burglary',      # Stolen property
        'vandalism',           # Property vandalism
        'storm_damage',        # Wind, hail, lightning
        'liability',           # Someone injured on property
        'personal_property',   # Damaged/lost belongings
        'structural_damage',   # Foundation, roof damage
        'mold_damage',         # Mold remediation
        'equipment_breakdown', # HVAC, appliances
    ],
    'life': [
        'death_benefit',       # Primary death claim
        'accidental_death',    # Accidental death benefit
        'terminal_illness',    # Accelerated benefit
        'disability_waiver',   # Waiver of premium
        'cash_value_withdrawal', # Policy loan/withdrawal
    ],
    'health': [
        'hospitalization',     # Hospital stay
        'surgery',             # Surgical procedures
        'emergency_room',      # ER visits
        'prescription_drugs',  # Medication costs
        'specialist_visit',    # Specialist consultations
        'diagnostic_testing',  # Lab work, imaging
        'mental_health',       # Therapy, psychiatry
        'physical_therapy',    # Rehabilitation
        'dental',              # Dental procedures
        'vision',              # Eye care
        'maternity',           # Pregnancy/childbirth
        'preventive_care',     # Checkups, vaccinations
    ]
}


def get_claim_types():
    """Get all available claim types"""
    return CLAIM_TYPES


def create_claim(policy_id, claim_number, claim_type, description, amount, filed_date, status='submitted'):
    """Create a new claim"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO claims (policy_id, claim_number, claim_type, description, amount, filed_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (policy_id, claim_number, claim_type, description, amount, filed_date, status))
    
    claim_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return claim_id


def get_all_claims():
    """Get all claims with policy and customer info"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT cl.*, p.policy_number, p.policy_type, c.name as customer_name, c.email as customer_email
        FROM claims cl
        JOIN policies p ON cl.policy_id = p.id
        JOIN customers c ON p.customer_id = c.id
        ORDER BY cl.filed_date DESC
    ''')
    
    claims = cursor.fetchall()
    conn.close()
    return [dict(row) for row in claims]


def get_claims_by_policy(policy_id):
    """Get claims for a specific policy"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM claims
        WHERE policy_id = ?
        ORDER BY filed_date DESC
    ''', (policy_id,))
    
    claims = cursor.fetchall()
    conn.close()
    return [dict(row) for row in claims]


def get_claim_by_id(claim_id):
    """Get a single claim by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM claims WHERE id = ?', (claim_id,))
    claim = cursor.fetchone()
    
    conn.close()
    return dict(claim) if claim else None


def update_claim(claim_id, claim_type, description, amount, status, resolved_date=None):
    """Update a claim"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE claims
        SET claim_type = ?, description = ?, amount = ?, status = ?, resolved_date = ?
        WHERE id = ?
    ''', (claim_type, description, amount, status, resolved_date, claim_id))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def delete_claim(claim_id):
    """Delete a claim"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM claims WHERE id = ?', (claim_id,))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


# ============================================
# RENEWAL ALERTS & EXPIRING POLICIES
# ============================================

def get_expiring_policies(days=30):
    """Get policies expiring within specified days"""
    conn = get_connection()
    cursor = conn.cursor()
    
    target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT p.*, c.name as customer_name, c.email as customer_email, c.phone as customer_phone
        FROM policies p
        JOIN customers c ON p.customer_id = c.id
        WHERE p.end_date BETWEEN ? AND ? AND p.status = 'active'
        ORDER BY p.end_date ASC
    ''', (today, target_date))
    
    policies = cursor.fetchall()
    conn.close()
    return [dict(row) for row in policies]


def get_renewal_alerts():
    """Get categorized renewal alerts by urgency"""
    urgent = get_expiring_policies(7)      # Within 7 days - critical
    warning = get_expiring_policies(14)    # Within 14 days
    notice = get_expiring_policies(30)     # Within 30 days
    
    # Filter to avoid duplicates
    warning_ids = {p['id'] for p in urgent}
    warning = [p for p in warning if p['id'] not in warning_ids]
    
    notice_ids = warning_ids | {p['id'] for p in warning}
    notice = [p for p in notice if p['id'] not in notice_ids]
    
    return {
        'urgent': urgent,      # 0-7 days
        'warning': warning,    # 8-14 days
        'notice': notice       # 15-30 days
    }


def get_claims_stats():
    """Get claims statistics for dashboard"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total claims
    cursor.execute('SELECT COUNT(*) FROM claims')
    total_claims = cursor.fetchone()[0]
    
    # Pending claims (submitted + reviewing)
    cursor.execute("SELECT COUNT(*) FROM claims WHERE status IN ('submitted', 'reviewing')")
    pending_claims = cursor.fetchone()[0]
    
    # Total claim amount (approved + paid)
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM claims WHERE status IN ('approved', 'paid')")
    total_claim_amount = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_claims': total_claims,
        'pending_claims': pending_claims,
        'total_claim_amount': round(total_claim_amount, 2)
    }


# ============================================
# NOTIFICATION TRACKING
# ============================================

def record_notification(policy_id, notification_type):
    """Record that a notification was sent"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO notifications (policy_id, notification_type)
        VALUES (?, ?)
    ''', (policy_id, notification_type))
    
    conn.commit()
    conn.close()


def get_policies_needing_notification(days_before_expiry, notification_type):
    """Get policies that need reminders and haven't been notified yet"""
    conn = get_connection()
    cursor = conn.cursor()
    
    target_date = (datetime.now() + timedelta(days=days_before_expiry)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT p.*, c.name as customer_name, c.email as customer_email
        FROM policies p
        JOIN customers c ON p.customer_id = c.id
        WHERE p.end_date BETWEEN ? AND ?
        AND p.status = 'active'
        AND p.id NOT IN (
            SELECT policy_id FROM notifications 
            WHERE notification_type = ?
            AND date(sent_at) = date('now')
        )
    ''', (today, target_date, notification_type))
    
    policies = cursor.fetchall()
    conn.close()
    return [dict(row) for row in policies]


# ============================================
# ANALYTICS & REPORTING
# ============================================

def get_policy_breakdown():
    """Get count of policies by type"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT policy_type, COUNT(*) as count, SUM(premium) as total_premium
        FROM policies
        WHERE status = 'active'
        GROUP BY policy_type
        ORDER BY count DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_revenue_by_month(months=6):
    """Get monthly revenue (premium) for the last N months"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', start_date) as month,
            SUM(premium) as revenue,
            COUNT(*) as policy_count
        FROM policies
        WHERE start_date >= date('now', '-' || ? || ' months')
        GROUP BY strftime('%Y-%m', start_date)
        ORDER BY month ASC
    ''', (months,))
    
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_claims_by_status():
    """Get claims grouped by status"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT status, COUNT(*) as count, SUM(amount) as total_amount
        FROM claims
        GROUP BY status
        ORDER BY count DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_claims_by_type():
    """Get claims grouped by type"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT claim_type, COUNT(*) as count, SUM(amount) as total_amount
        FROM claims
        GROUP BY claim_type
        ORDER BY count DESC
        LIMIT 10
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_customer_lifetime_value():
    """Get total premium value per customer (CLV)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            c.id,
            c.name,
            c.email,
            COUNT(p.id) as policy_count,
            COALESCE(SUM(p.premium), 0) as total_premium,
            MIN(p.start_date) as first_policy_date
        FROM customers c
        LEFT JOIN policies p ON c.id = p.customer_id
        GROUP BY c.id
        ORDER BY total_premium DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_monthly_report_data():
    """Get comprehensive data for monthly report"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Current month stats
    current_month = datetime.now().strftime('%Y-%m')
    
    # New customers this month
    cursor.execute('''
        SELECT COUNT(*) FROM customers 
        WHERE strftime('%Y-%m', created_at) = ?
    ''', (current_month,))
    new_customers = cursor.fetchone()[0]
    
    # New policies this month
    cursor.execute('''
        SELECT COUNT(*), COALESCE(SUM(premium), 0) FROM policies 
        WHERE strftime('%Y-%m', start_date) = ?
    ''', (current_month,))
    result = cursor.fetchone()
    new_policies = result[0]
    new_premium = result[1]
    
    # Claims filed this month
    cursor.execute('''
        SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM claims 
        WHERE strftime('%Y-%m', filed_date) = ?
    ''', (current_month,))
    result = cursor.fetchone()
    claims_filed = result[0]
    claims_amount = result[1]
    
    # Policies expiring this month
    cursor.execute('''
        SELECT COUNT(*) FROM policies 
        WHERE strftime('%Y-%m', end_date) = ? AND status = 'active'
    ''', (current_month,))
    expiring_policies = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'month': datetime.now().strftime('%B %Y'),
        'new_customers': new_customers,
        'new_policies': new_policies,
        'new_premium': round(new_premium, 2),
        'claims_filed': claims_filed,
        'claims_amount': round(claims_amount, 2),
        'expiring_policies': expiring_policies,
        'policy_breakdown': get_policy_breakdown(),
        'claims_by_status': get_claims_by_status(),
        'top_customers': get_customer_lifetime_value()[:10]
    }


# Initialize database when module is imported
if __name__ == '__main__':
    init_db()

