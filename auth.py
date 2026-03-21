from database import user_get_by_key, user_get_by_email, user_create
from security import (
    generate_api_key, hash_password, verify_password,
    is_valid_key_format, create_access_token,
    is_login_blocked, record_login_attempt, get_remaining_block_time
)
from validators import validate_email, validate_password
from logger import log_security


def validate_api_key(api_key):
    if not api_key:
        return None
    if not is_valid_key_format(api_key):
        log_security("invalid_key_format", detail="bad format")
        return None
    user = user_get_by_key(api_key)
    if not user:
        log_security("invalid_key", detail="not found")
        return None
    return user


def signup_user(email, password):
    valid_email, email_error = validate_email(email)
    if not valid_email:
        return {"success": False, "error": email_error}
    valid_pass, pass_error = validate_password(password)
    if not valid_pass:
        return {"success": False, "error": pass_error}
    existing = user_get_by_email(email)
    if existing:
        return {"success": False, "error": "Email already registered"}
    key1 = generate_api_key()
    key2 = generate_api_key()
    password_hash = hash_password(password)
    user = user_create(email.lower().strip(), password_hash, key1, key2)
    if "error" in user:
        return {"success": False, "error": "Could not create account. Try again."}
    token = create_access_token({"sub": email.lower().strip()})
    return {"success": True, "user": user, "api_key_1": key1, "api_key_2": key2, "access_token": token, "token_type": "bearer"}


def login_user(email, password, ip=""):
    identifier = email.lower().strip()
    if is_login_blocked(identifier):
        remaining = get_remaining_block_time(identifier)
        return {"success": False, "error": f"Too many failed attempts. Try again in {remaining // 60} minutes.", "blocked": True}
    user = user_get_by_email(email)
    if not user:
        record_login_attempt(identifier, success=False)
        return {"success": False, "error": "Invalid email or password"}
    if not verify_password(password, user["password"]):
        record_login_attempt(identifier, success=False)
        log_security("failed_login", detail=f"email={identifier[:20]}")
        return {"success": False, "error": "Invalid email or password"}
    record_login_attempt(identifier, success=True)
    token = create_access_token({"sub": identifier})
    return {"success": True, "user": {"id": user["id"], "email": user["email"], "api_key_1": user["api_key_1"], "api_key_2": user["api_key_2"], "password": user["password"]}, "access_token": token, "token_type": "bearer"}


def change_password(user_id, old_password, new_password, current_hash):
    if not verify_password(old_password, current_hash):
        return {"success": False, "error": "Current password incorrect"}
    valid_pass, pass_error = validate_password(new_password)
    if not valid_pass:
        return {"success": False, "error": pass_error}
    from database import user_update_password
    new_hash = hash_password(new_password)
    success = user_update_password(user_id, new_hash)
    if not success:
        return {"success": False, "error": "Failed to update password"}
    return {"success": True, "message": "Password updated successfully"}
