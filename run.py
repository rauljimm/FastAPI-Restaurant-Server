"""
Script de ejecución para el Sistema de Gestión de Restaurante con FastAPI
"""
import uvicorn
from app.core.config import SQLALCHEMY_DATABASE_URL, create_tables
from app.db.database import engine

if __name__ == "__main__":
    # Crear tablas antes de iniciar la aplicación
    create_tables()
    
    # Ejecutar la aplicación FastAPI
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 