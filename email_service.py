"""
Email Service Module

Handles email notifications for:
- Policy renewal reminders
- Claim status updates

Uses Python's smtplib with APScheduler for background jobs.
Configure SMTP settings below or use environment variables.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Email Configuration (set these for production)
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')  # For Gmail, use App Password
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'crm@insurancecompany.com')
COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Insurance CRM')

# Demo mode - if True, emails are logged instead of sent
DEMO_MODE = True


def send_email(to_email, subject, html_body, text_body=None):
    """
    Send an email. In demo mode, logs to console instead.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML content of the email
        text_body: Plain text fallback (optional)
    
    Returns:
        bool: True if sent/logged successfully
    """
    if DEMO_MODE:
        print(f"\n{'='*50}")
        print(f"📧 EMAIL NOTIFICATION (Demo Mode)")
        print(f"{'='*50}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        print(f"Body Preview: {html_body[:200]}...")
        print(f"{'='*50}\n")
        return True
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{COMPANY_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        
        if text_body:
            msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        
        print(f"✅ Email sent to {to_email}: {subject}")
        return True
    
    except Exception as e:
        print(f"❌ Email failed to {to_email}: {e}")
        return False


def send_renewal_reminder(policy, days_until_expiry):
    """
    Send a policy renewal reminder email.
    
    Args:
        policy: Dict with policy info including customer_name, customer_email, policy_number, end_date
        days_until_expiry: Number of days until policy expires
    """
    customer_name = policy.get('customer_name', 'Valued Customer')
    customer_email = policy.get('customer_email')
    policy_number = policy.get('policy_number', 'N/A')
    policy_type = policy.get('policy_type', 'Insurance').title()
    end_date = policy.get('end_date', 'N/A')
    
    if not customer_email:
        print(f"⚠️ No email for policy {policy_number}, skipping reminder")
        return False
    
    # Determine urgency level
    if days_until_expiry <= 7:
        urgency = "URGENT"
        urgency_color = "#ef4444"
    elif days_until_expiry <= 14:
        urgency = "IMPORTANT"
        urgency_color = "#f59e0b"
    else:
        urgency = "REMINDER"
        urgency_color = "#3b82f6"
    
    subject = f"[{urgency}] Your {policy_type} Policy Expires in {days_until_expiry} Days"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #1a1a2e, #0f3460); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
            .urgency-badge {{ background: {urgency_color}; color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .policy-box {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid {urgency_color}; margin: 20px 0; }}
            .btn {{ display: inline-block; background: {urgency_color}; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏢 {COMPANY_NAME}</h1>
                <span class="urgency-badge">{urgency}: ACTION REQUIRED</span>
            </div>
            <div class="content">
                <p>Dear <strong>{customer_name}</strong>,</p>
                
                <p>This is a reminder that your insurance policy is expiring soon:</p>
                
                <div class="policy-box">
                    <p><strong>Policy Number:</strong> {policy_number}</p>
                    <p><strong>Policy Type:</strong> {policy_type}</p>
                    <p><strong>Expiration Date:</strong> {end_date}</p>
                    <p><strong>Days Remaining:</strong> <span style="color: {urgency_color}; font-weight: bold;">{days_until_expiry} days</span></p>
                </div>
                
                <p>To ensure continuous coverage, please renew your policy before the expiration date.</p>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="#" class="btn">Renew Now</a>
                </p>
                
                <p>If you have any questions, please contact our support team.</p>
                
                <p>Best regards,<br><strong>{COMPANY_NAME} Team</strong></p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply directly to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Dear {customer_name},
    
    {urgency}: Your insurance policy is expiring soon!
    
    Policy Number: {policy_number}
    Policy Type: {policy_type}
    Expiration Date: {end_date}
    Days Remaining: {days_until_expiry} days
    
    Please renew your policy before the expiration date to ensure continuous coverage.
    
    Best regards,
    {COMPANY_NAME} Team
    """
    
    return send_email(customer_email, subject, html_body, text_body)


def send_claim_status_update(claim, old_status, new_status):
    """
    Send a claim status update email.
    
    Args:
        claim: Dict with claim info
        old_status: Previous status
        new_status: New status
    """
    customer_email = claim.get('customer_email')
    customer_name = claim.get('customer_name', 'Valued Customer')
    claim_number = claim.get('claim_number', 'N/A')
    
    if not customer_email:
        return False
    
    status_messages = {
        'submitted': ('Claim Received', 'Your claim has been submitted and is pending review.'),
        'reviewing': ('Under Review', 'Your claim is currently being reviewed by our team.'),
        'approved': ('Claim Approved! ✅', 'Great news! Your claim has been approved.'),
        'denied': ('Claim Status Update', 'Unfortunately, your claim has been denied. Please contact us for more information.'),
        'paid': ('Payment Processed 💰', 'Your claim payment has been processed.')
    }
    
    title, message = status_messages.get(new_status, ('Status Update', f'Your claim status has been updated to: {new_status}'))
    
    subject = f"Claim #{claim_number}: {title}"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Claim Status Update</h2>
        <p>Dear {customer_name},</p>
        <p>{message}</p>
        <p><strong>Claim Number:</strong> {claim_number}</p>
        <p><strong>New Status:</strong> {new_status.title()}</p>
        <p>Best regards,<br>{COMPANY_NAME} Team</p>
    </body>
    </html>
    """
    
    return send_email(customer_email, subject, html_body)


# ============================================
# BACKGROUND SCHEDULER
# ============================================

def run_renewal_check():
    """
    Check for expiring policies and send reminders.
    This should be called by the scheduler.
    """
    from database import get_policies_needing_notification, record_notification
    
    print(f"\n🔔 Running renewal check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check 30-day reminders
    policies_30 = get_policies_needing_notification(30, 'renewal_30day')
    for policy in policies_30:
        days = (datetime.strptime(policy['end_date'], '%Y-%m-%d') - datetime.now()).days
        if send_renewal_reminder(policy, days):
            record_notification(policy['id'], 'renewal_30day')
    
    # Check 14-day reminders
    policies_14 = get_policies_needing_notification(14, 'renewal_14day')
    for policy in policies_14:
        days = (datetime.strptime(policy['end_date'], '%Y-%m-%d') - datetime.now()).days
        if send_renewal_reminder(policy, days):
            record_notification(policy['id'], 'renewal_14day')
    
    # Check 7-day reminders (urgent)
    policies_7 = get_policies_needing_notification(7, 'renewal_7day')
    for policy in policies_7:
        days = (datetime.strptime(policy['end_date'], '%Y-%m-%d') - datetime.now()).days
        if send_renewal_reminder(policy, days):
            record_notification(policy['id'], 'renewal_7day')
    
    total_sent = len(policies_30) + len(policies_14) + len(policies_7)
    print(f"✅ Renewal check complete. {total_sent} reminders sent.\n")


def start_scheduler():
    """
    Start the background scheduler for automated tasks.
    Call this when the app starts.
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        
        scheduler = BackgroundScheduler()
        
        # Run renewal check every day at 9:00 AM
        scheduler.add_job(run_renewal_check, 'cron', hour=9, minute=0, id='renewal_check')
        
        # Also run once on startup (after 30 seconds delay)
        scheduler.add_job(run_renewal_check, 'date', 
                         run_date=datetime.now().replace(second=30),
                         id='startup_check')
        
        scheduler.start()
        print("📅 Background scheduler started. Renewal checks will run daily at 9:00 AM.")
        return scheduler
    
    except ImportError:
        print("⚠️ APScheduler not installed. Run: pip install apscheduler")
        print("   Email reminders will not be sent automatically.")
        return None
    except Exception as e:
        print(f"⚠️ Scheduler error: {e}")
        return None


# Manual trigger for testing
if __name__ == '__main__':
    print("Testing email service...")
    run_renewal_check()
