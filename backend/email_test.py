import smtplib

host = "smtp.office365.com"
port = 587
user = "rahulboy@amazon.com"
password = "3gxyp3YRgU@"

try:
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        print("SMTP connection successful!")
except Exception as e:
    print("SMTP connection failed:", e)