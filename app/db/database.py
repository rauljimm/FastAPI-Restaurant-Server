"""
Configuración de la sesión de la base de datos.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import SQLALCHEMY_DATABASE_URL

# Crear el motor de la base de datos
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Crear el sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear la clase base para los modelos
Base = declarative_base()

# Dependencia para obtener la sesión de la base de datos
def get_db():
    """
    Función de dependencia que proporciona una sesión de SQLAlchemy.
    Devuelve una sesión y asegura que se cierre después de su uso.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 