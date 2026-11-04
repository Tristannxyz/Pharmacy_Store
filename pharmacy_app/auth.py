import logging
from datetime import datetime, timedelta
import bcrypt
from config import MAX_LOGIN_ATTEMPTS, LOCKOUT_MINUTES, ROLE_PERMISSIONS
import db

logger = logging.getLogger(__name__)

class SessionManager:
    """Singleton session container for the logged-in user."""
    _current_user = None

    @classmethod
    def set_user(cls, user_dict):
        cls._current_user = user_dict

    @classmethod
    def get_user(cls):
        return cls._current_user

    @classmethod
    def get_user_id(cls):
        return cls._current_user["id"] if cls._current_user else None

    @classmethod
    def get_username(cls):
        return cls._current_user["username"] if cls._current_user else "anonymous"

    @classmethod
    def get_role(cls):
        return cls._current_user["role"] if cls._current_user else None

    @classmethod
    def is_authenticated(cls):
        return cls._current_user is not None

    @classmethod
    def clear(cls):
        cls._current_user = None

    @classmethod
    def has_permission(cls, perm_name):
        """Validates if active user role has the required permission."""
        if not cls._current_user:
            return False
        role = cls._current_user.get("role")
        allowed = ROLE_PERMISSIONS.get(role, [])
        return perm_name in allowed

def hash_password(plain_password: str) -> str:
    """Hashes a plain text password using bcrypt with a secure salt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def log_audit(action: str, details: str, user_id=None, username=None):
    """Inserts a tamper-resistant record into audit_log."""
    try:
        if not user_id and SessionManager.is_authenticated():
            user_id = SessionManager.get_user_id()
            username = SessionManager.get_username()

        query = """
            INSERT INTO audit_log (user_id, username, action, details)
            VALUES (%s, %s, %s, %s)
        """
        db.execute_query(query, (user_id, username, action, details), commit=True)
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}")

def authenticate_user(username: str, plain_password: str):
    """
    Validates user credentials against database.
    Enforces:
    - Account active check
    - Max 5 failed attempts lockout (15 minutes lockout)
    - Audit logging
    Returns: (success: bool, message: str, user_data: dict or None)
    """
    if not username or not plain_password:
        return False, "Username and password cannot be empty.", None

    user = db.execute_query(
        "SELECT * FROM users WHERE username = %s",
        (username,),
        fetchone=True
    )

    if not user:
        log_audit("FAILED_LOGIN", f"Non-existent username attempted: {username}")
        return False, "Invalid username or password.", None

    # Check if disabled
    if not user.get("is_active"):
        log_audit("FAILED_LOGIN", f"Disabled account attempted login: {username}", user["id"], username)
        return False, "Your account has been deactivated. Please contact an Administrator.", None

    now = datetime.now()

    # Check lockout
    locked_until = user.get("locked_until")
    if locked_until and locked_until > now:
        remaining = int((locked_until - now).total_seconds() / 60) + 1
        log_audit("BLOCKED_LOGIN", f"Account locked. {remaining} mins remaining", user["id"], username)
        return False, f"Account is locked due to too many failed attempts. Try again in {remaining} minute(s).", None

    # Verify Password
    if verify_password(plain_password, user["password_hash"]):
        # Reset failed attempts and update last login
        db.execute_query("""
            UPDATE users 
            SET failed_attempts = 0, locked_until = NULL, last_login = %s 
            WHERE id = %s
        """, (now, user["id"]), commit=True)

        user_info = {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "last_login": now
        }
        SessionManager.set_user(user_info)
        log_audit("LOGIN_SUCCESS", f"User {username} ({user['role']}) logged in successfully.", user["id"], username)
        return True, "Login successful.", user_info

    else:
        # Increment failed attempts
        failed_count = (user.get("failed_attempts") or 0) + 1
        if failed_count >= MAX_LOGIN_ATTEMPTS:
            lockout_time = now + timedelta(minutes=LOCKOUT_MINUTES)
            db.execute_query("""
                UPDATE users 
                SET failed_attempts = %s, locked_until = %s 
                WHERE id = %s
            """, (failed_count, lockout_time, user["id"]), commit=True)
            log_audit("ACCOUNT_LOCKED", f"Account locked for {LOCKOUT_MINUTES} mins after {failed_count} failed attempts.", user["id"], username)
            return False, f"Account locked! Too many failed attempts ({failed_count}/{MAX_LOGIN_ATTEMPTS}). Locked for {LOCKOUT_MINUTES} minutes.", None
        else:
            db.execute_query("""
                UPDATE users SET failed_attempts = %s WHERE id = %s
            """, (failed_count, user["id"]), commit=True)
            attempts_left = MAX_LOGIN_ATTEMPTS - failed_count
            log_audit("FAILED_LOGIN", f"Incorrect password. Attempts left: {attempts_left}", user["id"], username)
            return False, f"Invalid username or password. {attempts_left} attempt(s) remaining before account lockout.", None

def logout_user():
    """Logs out the active user and records the event in audit log."""
    if SessionManager.is_authenticated():
        log_audit("LOGOUT", f"User {SessionManager.get_username()} logged out.")
        SessionManager.clear()

