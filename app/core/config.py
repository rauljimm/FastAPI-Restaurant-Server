"""
Configuration settings for the application.
"""
from typing import List
from datetime import timedelta

# API configuration
API_V1_STR: str = "/api/v1"
PROJECT_NAME: str = "API de Gestión de Restaurante"
DESCRIPTION: str = "Sistema para coordinar operaciones entre camareros, cocineros y administradores"
VERSION: str = "1.0.0"

# CORS configuration
ALLOWED_ORIGINS: List[str] = ["*"]  
ALLOWED_METHODS: List[str] = ["*"]
ALLOWED_HEADERS: List[str] = ["*"]

# Database configuration
SQLALCHEMY_DATABASE_URL: str = "sqlite:///./restaurante.db"
SQLALCHEMY_TEST_DATABASE_URL: str = "sqlite:///./test_restaurante.db"

# Authentication configuration
JWT_SECRET_KEY: str = "clave_super_secreta"  
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas
TOKEN_URL: str = "/token" 

def create_tables():
    """Create database tables."""
    from app.db.database import Base, engine
    from app.models import usuario, mesa, categoria, producto, pedido, reserva
    Base.metadata.create_all(bind=engine)
    print("Database tables created.") 