import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")

def send_email(to_email, subject, html_body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}. Error: {e}")

def send_leave_email(to_email, associate_name, leave_type, start_date, end_date, status, backup_name):
    """Send email to associate for leave update."""
    if status.lower() == "rejected":
        return  # Skip sending rejected emails

    subject_prefix = "✅ Leave Approved" if status.lower() == "approved" else "🕒 Leave Pending"
    color = "green" if status.lower() == "approved" else "orange"
    header = "Your Leave Has Been Approved" if status.lower() == "approved" else "Your Leave Is Under Review"

    subject = f"{subject_prefix}: {start_date} to {end_date}"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
      <h2 style="color: {color};">{header}</h2>
      <p>Hi <strong>{associate_name}</strong>,</p>
      <p>Your leave request for the below period is currently <strong>{status.capitalize()}</strong>.</p>
      <table style="border-collapse: collapse; width: 100%; margin-top: 10px;">
        <tr><td><strong>Leave Type:</strong></td><td>{leave_type}</td></tr>
        <tr><td><strong>Start Date:</strong></td><td>{start_date}</td></tr>
        <tr><td><strong>End Date:</strong></td><td>{end_date}</td></tr>
        <tr><td><strong>Backup Assigned:</strong></td><td>{backup_name}</td></tr>
        <tr><td><strong>Status:</strong></td><td style="color: {color};"><strong>{status.capitalize()}</strong></td></tr>
      </table>
      <p style="margin-top: 20px;">{"Have a great day!" if status.lower() == "approved" else "You will receive another update once a manager reviews it."}</p>
      <p>Regards,<br>Leave Management System</p>
    </body>
    </html>
    """
    send_email(to_email, subject, html_body)

def send_manager_email(to_email, associate_name, leave_type, start_date, end_date, backup_name, reason="Pending due to system rules"):
    """Send email to manager for pending leave approval."""
    subject = f"⚠️ Action Required: Leave Pending for {associate_name}"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
      <h2 style="color: orange;">Pending Leave Request</h2>
      <p>Hi Manager,</p>
      <p><strong>{associate_name}</strong> has submitted a leave request pending your approval.</p>
      <table style="border-collapse: collapse; width: 100%; margin-top: 10px;">
        <tr><td><strong>Leave Type:</strong></td><td>{leave_type}</td></tr>
        <tr><td><strong>Start Date:</strong></td><td>{start_date}</td></tr>
        <tr><td><strong>End Date:</strong></td><td>{end_date}</td></tr>
        <tr><td><strong>Backup Person:</strong></td><td>{backup_name}</td></tr>
        <tr><td><strong>Reason for Pending:</strong></td><td>{reason}</td></tr>
      </table>
      <p style="margin-top: 20px;">Please log in to review and approve this leave.</p>
      <p>Regards,<br>Leave Management System</p>
    </body>
    </html>
    """
    send_email(to_email, subject, html_body)