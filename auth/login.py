# Vernika Application - Login Logic
# Authentication handling for multi-user login

from database.connection import get_session
from database.models import User
from database.operations import get_user_by_username, create_audit_log
from config import ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY
from datetime import datetime, timedelta

# Try to import PyJWT, fall back to python-jose if not available
try:
    import jwt
except ImportError:
    try:
        from jose import jwt  # type: ignore
    except ImportError:
        jwt = None
        print("WARNING: Neither PyJWT nor python-jose is installed. JWT functionality will not work.")


class LoginResult:
    """Login result container"""

    def __init__(self, success: bool, user: User = None, error: str = None, token: str = None):
        self.success = success
        self.user = user
        self.error = error
        self.token = token


def authenticate_user(username: str, password: str) -> LoginResult:
    """
    Authenticate user with username and password
    Returns LoginResult with success status and user info
    """
    with get_session() as session:
        try:
            # Get user by username
            user = get_user_by_username(session, username)

            # Check if user exists
            if not user:
                return LoginResult(
                    success=False,
                    error="Invalid username or password"
                )

            # Check if user is active
            if not user.is_active_user():
                return LoginResult(
                    success=False,
                    error="Account is deactivated. Please contact administrator."
                )

            # Verify password
            if not user.check_password(password):
                # Log failed login attempt
                create_audit_log(
                    session,
                    user_id=user.id,
                    action="LOGIN_FAILED",
                    details=f"Failed login attempt for user: {username}"
                )
                return LoginResult(
                    success=False,
                    error="Invalid username or password"
                )

            # Generate access token
            access_token = create_access_token(
                data={"sub": user.username,
                      "role": user.role.name, "user_id": user.id}
            )

            # Log successful login
            create_audit_log(
                session,
                user_id=user.id,
                action="LOGIN_SUCCESS",
                details=f"User {username} logged in successfully"
            )

            return LoginResult(
                success=True,
                user=user,
                token=access_token
            )

        except Exception as e:
            return LoginResult(
                success=False,
                error=f"Authentication error: {str(e)}"
            )


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create JWT access token
    """
    if jwt is None:
        raise ImportError(
            "JWT library not installed. Please install PyJWT or python-jose")

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token
    """
    if jwt is None:
        print("WARNING: JWT library not installed. Token validation failed.")
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def validate_session(token: str) -> LoginResult:
    """
    Validate existing session token
    """
    payload = decode_token(token)

    if not payload:
        return LoginResult(
            success=False,
            error="Invalid or expired session"
        )

    with get_session() as session:
        try:
            user = get_user_by_username(session, payload.get("sub"))

            if not user:
                return LoginResult(
                    success=False,
                    error="User not found"
                )

            if not user.is_active_user():
                return LoginResult(
                    success=False,
                    error="Account is deactivated"
                )

            return LoginResult(
                success=True,
                user=user,
                token=token
            )

        except Exception as e:
            return LoginResult(
                success=False,
                error=f"Session validation error: {str(e)}"
            )


def logout_user(token: str) -> bool:
    """
    Logout user and invalidate session
    """
    payload = decode_token(token)

    if payload:
        with get_session() as session:
            try:
                user = get_user_by_username(session, payload.get("sub"))
                if user:
                    create_audit_log(
                        session,
                        user_id=user.id,
                        action="LOGOUT",
                        details=f"User {user.username} logged out"
                    )
                return True
            except Exception:
                return False

    return True
