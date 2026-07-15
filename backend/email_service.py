import smtplib
from email.mime.text import MIMEText

def send_email(to_email, subject, body):
    """
    Sends an email using localhost SMTP server.
    """
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = "admin@ppa.com"
        msg['To'] = to_email
        
        with smtplib.SMTP('localhost', 1025) as server:
            server.send_message(msg)
            print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"SMTP error (Mailhog not running?): {e}")
