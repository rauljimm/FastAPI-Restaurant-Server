"""
Security utilities.
"""
import bcrypt

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that a plain password matches a hashed password.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') 