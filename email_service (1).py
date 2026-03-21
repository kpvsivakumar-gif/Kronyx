import resend
from typing import Optional
from config import RESEND_API_KEY, FROM_EMAIL, FROM_NAME, APP_URL, APP_NAME, APP_VERSION, SUPPORT_EMAIL
from logger import log_error, log_info, log_warning

resend.api_key = RESEND_API_KEY


# ============================================================
# BASE EMAIL SENDER
# ============================================================

def send_email(to: str, subject: str, html: str, text: str = "") -> bool:
    try:
        if not RESEND_API_KEY:
            log_warning("RESEND_API_KEY not set - email not sent")
            return False
        if not to or not subject or not html:
            log_warning("Email missing required fields")
            return False
        payload = {
            "from": FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html
        }
        if text:
            payload["text"] = text
        resend.Emails.send(payload)
        log_info(f"Email sent to {to[:20]}... subject={subject[:30]}")
        return True
    except Exception as e:
        log_error(f"Email send failed: {e}", context="email_service")
        return False


# ============================================================
# EMAIL TEMPLATES
# ============================================================

def _base_styles() -> str:
    return """
    <style>
        body { font-family: 'Arial', sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #0D9488, #7C3AED); padding: 32px; text-align: center; }
        .header h1 { color: white; margin: 0; font-size: 28px; letter-spacing: 3px; }
        .header p { color: rgba(255,255,255,0.8); margin: 8px 0 0; font-size: 13px; }
        .body { padding: 32px; }
        .body h2 { color: #1A1A2E; margin-top: 0; }
        .body p { color: #555; line-height: 1.6; }
        .key-box { background: #f8f8f8; border: 1px solid #e0e0e0; border-radius: 6px; padding: 16px; margin: 16px 0; font-family: monospace; font-size: 14px; word-break: break-all; }
        .key-label { font-size: 11px; color: #888; margin-bottom: 6px; font-family: Arial; }
        .btn { display: inline-block; background: #0D9488; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 16px 0; }
        .btn:hover { background: #0b7a70; }
        .alert-box { background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 16px; margin: 16px 0; }
        .danger-box { background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 6px; padding: 16px; margin: 16px 0; }
        .success-box { background: #d4edda; border: 1px solid #c3e6cb; border-radius: 6px; padding: 16px; margin: 16px 0; }
        .footer { background: #f8f8f8; padding: 20px 32px; border-top: 1px solid #eee; }
        .footer p { color: #999; font-size: 11px; margin: 4px 0; }
        .footer a { color: #0D9488; text-decoration: none; }
    </style>
    """


def _footer_html() -> str:
    return f"""
    <div class="footer">
        <p>{APP_NAME} v{APP_VERSION} &mdash; <a href="{APP_URL}">{APP_URL}</a></p>
        <p>Need help? <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
        <p style="color:#cc0000;font-weight:bold;">KRONYX is not responsible for any losses caused by AI outputs. Use responsibly.</p>
        <p>
            <a href="{APP_URL}/terms">Terms of Service</a> &middot;
            <a href="{APP_URL}/privacy">Privacy Policy</a> &middot;
            <a href="{APP_URL}/aup">Acceptable Use Policy</a>
        </p>
    </div>
    """


def _build_email(content: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {_base_styles()}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>KRONYX</h1>
                <p>The AWS of AI Infrastructure</p>
            </div>
            <div class="body">
                {content}
            </div>
            {_footer_html()}
        </div>
    </body>
    </html>
    """


# ============================================================
# SPECIFIC EMAIL FUNCTIONS
# ============================================================

def send_welcome(to_email: str, key1: str, key2: str) -> bool:
    masked1 = key1[:12] + "****" + key1[-4:] if len(key1) > 16 else key1[:8] + "****"
    masked2 = key2[:12] + "****" + key2[-4:] if len(key2) > 16 else key2[:8] + "****"
    content = f"""
    <h2>Welcome to KRONYX</h2>
    <p>Your account has been created successfully. You have <strong>2 API keys</strong> ready to use.</p>
    <p>These keys give you access to all 54 KRONYX capabilities including 5 Elite Pillars, 14 God Systems, 24 Layers and 11 Elite Features.</p>

    <div class="key-box">
        <div class="key-label">API KEY 1 (Primary)</div>
        {masked1}
    </div>
    <div class="key-box">
        <div class="key-label">API KEY 2 (Backup)</div>
        {masked2}
    </div>

    <div class="danger-box">
        <strong>Security Warning</strong><br>
        Never share your API keys publicly. Never commit them to GitHub. Never send them in chat.
        Your full keys are shown once in your dashboard. If compromised, regenerate immediately.
    </div>

    <h3>Quick Start</h3>
    <p>Make your first API call:</p>
    <div class="key-box">
        <div class="key-label">Example Request</div>
        curl -X POST {APP_URL}/v1/nexus-core/memex/remember \\<br>
        &nbsp;&nbsp;-H "X-API-Key: YOUR_API_KEY" \\<br>
        &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
        &nbsp;&nbsp;-d '{{"content": "Hello KRONYX", "user_id": "user_001"}}'
    </div>

    <a href="{APP_URL}/dashboard" class="btn">Open Dashboard</a>
    <a href="{APP_URL}/docs" class="btn" style="background:#7C3AED;margin-left:12px;">View API Docs</a>

    <p style="color:#888;font-size:12px;">By using KRONYX you agree to our Terms of Service and Acceptable Use Policy.</p>
    """
    html = _build_email(content)
    return send_email(to_email, f"Welcome to KRONYX - Your API Keys Are Ready", html)


def send_key_regenerated(to_email: str, new_key: str, key_number: int) -> bool:
    masked = new_key[:12] + "****" + new_key[-4:] if len(new_key) > 16 else new_key[:8] + "****"
    content = f"""
    <h2>API Key {key_number} Has Been Regenerated</h2>

    <div class="alert-box">
        <strong>Action Required</strong><br>
        Your old API Key {key_number} has been permanently deactivated. Any code still using the old key will fail immediately.
        Update your code with the new key as soon as possible.
    </div>

    <p>Your new Key {key_number} starts with:</p>
    <div class="key-box">
        <div class="key-label">NEW API KEY {key_number} (partial)</div>
        {masked}
    </div>

    <p>View your complete new key in your dashboard:</p>
    <a href="{APP_URL}/dashboard" class="btn">Go to Dashboard</a>

    <div class="danger-box">
        <strong>Not you?</strong><br>
        If you did not request this key regeneration, your account may be compromised.
        Change your password immediately and contact support at {SUPPORT_EMAIL}.
    </div>
    """
    html = _build_email(content)
    return send_email(to_email, f"KRONYX - API Key {key_number} Regenerated - Action Required", html)


def send_security_alert(to_email: str, threat_type: str, detail: str = "", ip: str = "") -> bool:
    content = f"""
    <h2 style="color:#cc0000;">Security Alert: Threat Blocked</h2>
    <p>KRONYX AEGIS SHIELD detected and blocked a security threat on your account.</p>

    <div class="danger-box">
        <strong>Threat Type:</strong> {threat_type}<br>
        {"<strong>Detail:</strong> " + detail[:200] + "<br>" if detail else ""}
        {"<strong>Source IP:</strong> " + ip[:50] + "<br>" if ip else ""}
        <strong>Status:</strong> BLOCKED - No data was accessed
    </div>

    <h3>What was blocked?</h3>
    <ul>
        <li>The malicious request was intercepted by VAULT layer</li>
        <li>No data was compromised</li>
        <li>The threat has been logged for analysis</li>
    </ul>

    <h3>Recommended Actions</h3>
    <ul>
        <li>Review your API key usage in the dashboard</li>
        <li>If you did not make this request, regenerate your API keys immediately</li>
        <li>Enable webhook alerts for real-time threat notifications</li>
    </ul>

    <a href="{APP_URL}/dashboard" class="btn">View Security Report</a>
    """
    html = _build_email(content)
    return send_email(to_email, "KRONYX Security Alert - Threat Blocked", html)


def send_password_changed(to_email: str) -> bool:
    content = f"""
    <h2>Password Changed Successfully</h2>

    <div class="success-box">
        Your KRONYX account password was changed successfully.
    </div>

    <div class="danger-box">
        <strong>Not you?</strong><br>
        If you did not change your password, your account may be compromised.
        Contact support immediately at {SUPPORT_EMAIL}.
    </div>

    <a href="{APP_URL}/dashboard" class="btn">Open Dashboard</a>
    """
    html = _build_email(content)
    return send_email(to_email, "KRONYX - Password Changed", html)


def send_rate_limit_warning(to_email: str, used: int, limit: int) -> bool:
    percentage = round((used / limit) * 100, 1) if limit > 0 else 0
    content = f"""
    <h2>API Usage Alert</h2>
    <p>You have used <strong>{used:,} of {limit:,}</strong> ({percentage}%) of your daily API limit.</p>

    <div class="alert-box">
        Your limit resets at midnight UTC. Consider upgrading your plan for higher limits.
    </div>

    <h3>Your Current Usage</h3>
    <div style="background:#f0f0f0;border-radius:4px;height:20px;margin:8px 0;">
        <div style="background:#0D9488;height:20px;border-radius:4px;width:{min(100, percentage)}%;"></div>
    </div>
    <p>{used:,} used / {limit:,} limit</p>

    <a href="{APP_URL}/dashboard" class="btn">Upgrade Plan</a>
    """
    html = _build_email(content)
    return send_email(to_email, f"KRONYX - API Usage at {percentage}% of Daily Limit", html)


def send_account_deactivated(to_email: str, reason: str = "") -> bool:
    content = f"""
    <h2>Account Deactivated</h2>

    <div class="danger-box">
        Your KRONYX account has been deactivated.
        {"<br>Reason: " + reason if reason else ""}
    </div>

    <p>If you believe this is an error, contact our support team at {SUPPORT_EMAIL}</p>
    """
    html = _build_email(content)
    return send_email(to_email, "KRONYX - Account Deactivated", html)


def send_new_feature_announcement(to_email: str, feature_name: str, feature_description: str) -> bool:
    content = f"""
    <h2>New Feature: {feature_name}</h2>
    <p>{feature_description}</p>

    <a href="{APP_URL}/docs" class="btn">View Documentation</a>
    <a href="{APP_URL}/dashboard" class="btn" style="background:#7C3AED;margin-left:12px;">Open Dashboard</a>
    """
    html = _build_email(content)
    return send_email(to_email, f"KRONYX - New Feature: {feature_name}", html)


def send_drift_alert(to_email: str, ai_id: str, drift_types: list) -> bool:
    drift_list = "".join([f"<li>{d}</li>" for d in drift_types])
    content = f"""
    <h2>DRIFTGUARD Alert: Behavioral Drift Detected</h2>
    <p>KRONYX DRIFTGUARD has detected significant behavioral drift in your AI <strong>{ai_id}</strong>.</p>

    <div class="danger-box">
        <strong>Drift Types Detected:</strong>
        <ul>{drift_list}</ul>
    </div>

    <p>This means your AI is behaving differently from its established baseline.
    This can affect user experience, safety, and compliance.</p>

    <h3>Recommended Actions</h3>
    <ul>
        <li>Review recent changes to your AI configuration</li>
        <li>Check if the underlying model was updated</li>
        <li>Consider establishing a new baseline if the drift is intentional</li>
    </ul>

    <a href="{APP_URL}/dashboard" class="btn">View Drift Report</a>
    """
    html = _build_email(content)
    return send_email(to_email, f"KRONYX DRIFTGUARD Alert - {ai_id}", html)
