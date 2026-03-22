from typing import Optional, Dict, Tuple
from database import (
    user_get_by_key, user_get_by_email, user_create,
    user_update_password, user_update_key, user_exists
)
from security import (
    generate_api_key, hash_password, verify_password,
    is_valid_key_format, create_access_token, create_refresh_token,
    is_login_blocked, record_login_attempt, get_remaining_block_seconds,
    get_login_attempts_count
)
from validators import validate_email, validate_password, validate_api_key_format
from logger import log_security, log_error, log_new_user, log_api_key_regenerated


# ============================================================
# API KEY VALIDATION
# ============================================================

def validate_api_key(api_key: str) -> Optional[Dict]:
    if not api_key:
        return None
    if not is_valid_key_format(api_key):
        log_security("invalid_key_format", detail="bad format on attempt")
        return None
    user = user_get_by_key(api_key)
    if not user:
        log_security("invalid_key", detail="key not found")
        return None
    if not user.get("is_active", True):
        log_security("inactive_account", api_key=api_key, detail="account deactivated")
        return None
    return user


# ============================================================
# USER SIGNUP
# ============================================================

def signup_user(email: str, password: str) -> Dict:
    try:
        valid_email, email_error = validate_email(email)
        if not valid_email:
            return {"success": False, "error": email_error}
        valid_pass, pass_error = validate_password(password)
        if not valid_pass:
            return {"success": False, "error": pass_error}
        email_clean = email.lower().strip()
        if user_exists(email_clean):
            return {"success": False, "error": "Email already registered. Please login instead."}
        key1 = generate_api_key()
        key2 = generate_api_key()
        password_hash = hash_password(password)
        user = user_create(email_clean, password_hash, key1, key2)
        if "error" in user:
            return {"success": False, "error": f"Account creation failed: {user['error'][:200]}"}
        token = create_access_token({"sub": email_clean, "user_id": str(user.get("id", ""))})
        refresh = create_refresh_token({"sub": email_clean})
        log_new_user(email_clean)
        return {
            "success": True,
            "user": {
                "id": user.get("id", ""),
                "email": user.get("email", ""),
                "plan": user.get("plan", "free")
            },
            "api_key_1": key1,
            "api_key_2": key2,
            "access_token": token,
            "refresh_token": refresh,
            "token_type": "bearer"
        }
    except Exception as e:
        log_error(str(e), context="signup_user")
        return {"success": False, "error": f"Signup error: {str(e)[:200]}"}


# ============================================================
# USER LOGIN
# ============================================================

def login_user(email: str, password: str, ip: str = "") -> Dict:
    try:
        if not email or not password:
            return {"success": False, "error": "Email and password are required"}
        identifier = email.lower().strip()
        if is_login_blocked(identifier):
            remaining = get_remaining_block_seconds(identifier)
            minutes = remaining // 60
            seconds = remaining % 60
            return {
                "success": False,
                "error": f"Too many failed login attempts. Try again in {minutes}m {seconds}s.",
                "blocked": True,
                "retry_after_seconds": remaining
            }
        user = user_get_by_email(email)
        if not user:
            record_login_attempt(identifier, success=False)
            attempts = get_login_attempts_count(identifier)
            remaining_attempts = max(0, 5 - attempts)
            return {
                "success": False,
                "error": "Invalid email or password",
                "remaining_attempts": remaining_attempts
            }
        if not verify_password(password, user.get("password", "")):
            record_login_attempt(identifier, success=False)
            log_security("failed_login", detail=f"email={identifier[:20]}")
            attempts = get_login_attempts_count(identifier)
            remaining_attempts = max(0, 5 - attempts)
            return {
                "success": False,
                "error": "Invalid email or password",
                "remaining_attempts": remaining_attempts
            }
        if not user.get("is_active", True):
            return {"success": False, "error": "Account is deactivated. Contact support."}
        record_login_attempt(identifier, success=True)
        token = create_access_token({"sub": identifier, "user_id": str(user.get("id", ""))})
        refresh = create_refresh_token({"sub": identifier})
        return {
            "success": True,
            "user": {
                "id": user.get("id", ""),
                "email": user.get("email", ""),
                "plan": user.get("plan", "free"),
                "api_key_1": user.get("api_key_1", ""),
                "api_key_2": user.get("api_key_2", ""),
                "password": user.get("password", "")
            },
            "access_token": token,
            "refresh_token": refresh,
            "token_type": "bearer"
        }
    except Exception as e:
        log_error(str(e), context="login_user")
        return {"success": False, "error": "Login failed. Please try again."}


# ============================================================
# PASSWORD CHANGE
# ============================================================

def change_password(user_id: str, old_password: str, new_password: str, current_hash: str) -> Dict:
    try:
        if not verify_password(old_password, current_hash):
            return {"success": False, "error": "Current password is incorrect"}
        valid_pass, pass_error = validate_password(new_password)
        if not valid_pass:
            return {"success": False, "error": pass_error}
        if old_password == new_password:
            return {"success": False, "error": "New password must be different from current password"}
        new_hash = hash_password(new_password)
        success = user_update_password(user_id, new_hash)
        if not success:
            return {"success": False, "error": "Failed to update password. Please try again."}
        return {"success": True, "message": "Password updated successfully"}
    except Exception as e:
        log_error(str(e), context="change_password")
        return {"success": False, "error": "Password change failed. Please try again."}


# ============================================================
# API KEY REGENERATION
# ============================================================

def regenerate_api_key(user_id: str, key_number: int) -> Dict:
    try:
        if key_number not in [1, 2]:
            return {"success": False, "error": "key_number must be 1 or 2"}
        new_key = generate_api_key()
        success = user_update_key(user_id, key_number, new_key)
        if not success:
            return {"success": False, "error": "Failed to regenerate key"}
        log_api_key_regenerated(new_key, key_number)
        return {"success": True, "new_key": new_key, "key_number": key_number}
    except Exception as e:
        log_error(str(e), context="regenerate_api_key")
        return {"success": False, "error": "Key regeneration failed"}
