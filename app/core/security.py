"""
Utilidades de seguridad.
"""
import bcrypt

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica que una contraseña sin formato coincida con una contraseña hasheada.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') 