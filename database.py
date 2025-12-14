"""
Database Module - SQLite Setup & Operations

Demonstrates:
- SQLite database connection
- Table creation with SQL
- CRUD helper functions
- Pagination
- Policy management
- Dashboard statistics
"""

import sqlite3
import os
from datetime import datetime, timedelta

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
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")


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
    
    conn.close()
    
    return {
        'total_customers': total_customers,
        'total_policies': total_policies,
        'active_policies': active_policies,
        'expiring_soon': expiring_soon,
        'total_premium': round(total_premium, 2)
    }


# Initialize database when module is imported
if __name__ == '__main__':
    init_db()
