import resend
from config import RESEND_API_KEY, FROM_EMAIL, APP_URL
from logger import log, log_error

resend.api_key = RESEND_API_KEY


def send_email(to, subject, html):
    try:
        if not RESEND_API_KEY:
            log.warning("RESEND_API_KEY not set")
            return False
        resend.Emails.send({"from": FROM_EMAIL, "to": [to], "subject": subject, "html": html})
        return True
    except Exception as e:
        log_error(f"Email send failed: {e}", context="email_service")
        return False


def footer():
    return f"""
    <hr style="margin:20px 0;border:none;border-top:1px solid #eee;">
    <p style="font-size:11px;color:#999;margin:0;">
    KRONYX &mdash; {APP_URL}<br>
    KRONYX is not responsible for any losses caused by AI outputs. Use at your own risk.
    <a href="{APP_URL}/terms" style="color:#999;">Terms</a> &middot;
    <a href="{APP_URL}/privacy" style="color:#999;">Privacy</a>
    </p>
    """


def send_welcome(to_email, key1, key2):
    masked1 = key1[:12] + "****"
    masked2 = key2[:12] + "****"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
    <h2>Welcome to KRONYX</h2>
    <p>Your account is ready. You have 2 API keys for 2 projects.</p>
    <div style="background:#f5f5f5;padding:16px;border-radius:4px;margin:16px 0;">
    <p style="margin:4px 0;font-family:monospace;"><strong>Key 1:</strong> {masked1}</p>
    <p style="margin:4px 0;font-family:monospace;"><strong>Key 2:</strong> {masked2}</p>
    </div>
    <p style="color:#cc0000;">Never share your API keys publicly or commit them to GitHub.</p>
    <p>Visit your dashboard to copy your full keys:</p>
    <a href="{APP_URL}/dashboard" style="background:#000;color:#fff;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block;">Open Dashboard</a>
    <br><br>
    <p style="font-size:13px;"><strong>Quick start:</strong></p>
    <pre style="background:#f5f5f5;padding:12px;font-size:12px;border-radius:4px;">
import httpx
KRONYX_URL = "https://your-app.railway.app"
headers = {{"X-API-Key": "your_key_here"}}
    </pre>
    {footer()}
    </div>
    """
    return send_email(to_email, "Welcome to KRONYX - Your API Keys Are Ready", html)


def send_key_regenerated(to_email, new_key, key_number):
    masked = new_key[:12] + "****"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
    <h2>API Key {key_number} Regenerated</h2>
    <div style="background:#fff3cd;border:1px solid #ffc107;padding:16px;border-radius:4px;margin:16px 0;">
    <p style="margin:0;font-weight:bold;">Action Required</p>
    <p style="margin:8px 0 0;">Your old key is permanently deactivated. Update your code immediately.</p>
    </div>
    <p>New key starts with: <code style="background:#f5f5f5;padding:2px 6px;">{masked}</code></p>
    <a href="{APP_URL}/dashboard" style="background:#000;color:#fff;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block;">Open Dashboard</a>
    <br><br>
    <p style="font-size:13px;color:#666;">If you did not request this, regenerate your key again immediately.</p>
    {footer()}
    </div>
    """
    return send_email(to_email, f"KRONYX - API Key {key_number} Regenerated", html)


def send_security_alert(to_email, threat_type, detail=""):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
    <h2 style="color:#cc0000;">Security Alert</h2>
    <p>KRONYX VAULT detected and blocked a security threat on your account.</p>
    <div style="background:#f8d7da;border:1px solid #f5c6cb;padding:16px;border-radius:4px;margin:16px 0;">
    <p style="margin:0;"><strong>Threat Type:</strong> {threat_type}</p>
    {f'<p style="margin:8px 0 0;"><strong>Detail:</strong> {detail[:100]}</p>' if detail else ''}
    </div>
    <a href="{APP_URL}/dashboard/vault" style="background:#000;color:#fff;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block;">View Security Report</a>
    {footer()}
    </div>
    """
    return send_email(to_email, "KRONYX Security Alert - Threat Blocked", html)


def send_health_alert(to_email, issue):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
    <h2>Health Alert</h2>
    <p>KRONYX PULSE detected an issue with your AI.</p>
    <div style="background:#f5f5f5;padding:16px;border-radius:4px;margin:16px 0;">
    <p style="margin:0;"><strong>Issue:</strong> {issue[:200]}</p>
    </div>
    <a href="{APP_URL}/dashboard/pulse" style="background:#000;color:#fff;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block;">View Health Report</a>
    {footer()}
    </div>
    """
    return send_email(to_email, "KRONYX - Health Alert Detected", html)


def send_rate_limit_warning(to_email, used, limit):
    percent = round((used / limit) * 100)
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
    <h2>API Usage Warning</h2>
    <p>You have used {percent}% of your daily API limit.</p>
    <div style="background:#fff3cd;border:1px solid #ffc107;padding:16px;border-radius:4px;margin:16px 0;">
    <p style="margin:0;"><strong>Used:</strong> {used:,} / {limit:,} calls</p>
    <p style="margin:8px 0 0;"><strong>Remaining:</strong> {limit - used:,} calls</p>
    <p style="margin:8px 0 0;">Limit resets at midnight UTC.</p>
    </div>
    <a href="{APP_URL}/dashboard" style="background:#000;color:#fff;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block;">View Dashboard</a>
    {footer()}
    </div>
    """
    return send_email(to_email, "KRONYX - API Usage Warning", html)


def send_export_ready(to_email, export_url):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
    <h2>Your Data Export is Ready</h2>
    <p>Your KRONYX data export has been prepared and is ready for download.</p>
    <a href="{export_url}" style="background:#000;color:#fff;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block;">Download Export</a>
    <p style="font-size:13px;color:#666;margin-top:16px;">This link expires in 24 hours.</p>
    {footer()}
    </div>
    """
    return send_email(to_email, "KRONYX - Data Export Ready", html)


def send_account_deleted(to_email):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
    <h2>Account Deleted</h2>
    <p>Your KRONYX account has been permanently deleted.</p>
    <p>Your data will be completely removed within 90 days as per our Privacy Policy.</p>
    <p>Thank you for using KRONYX.</p>
    {footer()}
    </div>
    """
    return send_email(to_email, "KRONYX - Account Deleted", html)


def send_password_changed(to_email):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
    <h2>Password Changed</h2>
    <p>Your KRONYX account password was successfully changed.</p>
    <p style="color:#cc0000;">If you did not make this change, contact us immediately and change your password.</p>
    <a href="{APP_URL}/dashboard" style="background:#000;color:#fff;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block;">Open Dashboard</a>
    {footer()}
    </div>
    """
    return send_email(to_email, "KRONYX - Password Changed", html)
