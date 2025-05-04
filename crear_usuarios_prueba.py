"""
Script para crear usuarios de prueba en la base de datos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from datetime import datetime, UTC

from app.db.database import engine, SessionLocal
from app.models.usuario import Usuario
from app.core.enums import RolUsuario
from app.core.security import get_password_hash

def crear_usuarios_prueba():
    """Crear usuarios de prueba con diferentes roles"""
    db = SessionLocal()
    
    try:
        # Verificar si ya existen usuarios
        usuarios_count = db.query(Usuario).count()
        if usuarios_count > 0:
            print("Ya existen usuarios en la base de datos. No se crearán usuarios de prueba.")
            return
        
        # Definir usuarios de prueba
        usuarios_prueba = [
            {
                "username": "admin",
                "email": "admin@example.com",
                "hashed_password": get_password_hash("admin123"),
                "nombre": "Admin",
                "apellido": "User",
                "rol": RolUsuario.ADMIN,
                "activo": True,
                "fecha_creacion": datetime.now(UTC)
            },
            {
                "username": "camarero",
                "email": "camarero@example.com",
                "hashed_password": get_password_hash("camarero123"),
                "nombre": "Camarero",
                "apellido": "User",
                "rol": RolUsuario.CAMARERO,
                "activo": True,
                "fecha_creacion": datetime.now(UTC)
            },
            {
                "username": "cocinero",
                "email": "cocinero@example.com",
                "hashed_password": get_password_hash("cocinero123"),
                "nombre": "Cocinero",
                "apellido": "User",
                "rol": RolUsuario.COCINERO,
                "activo": True,
                "fecha_creacion": datetime.now(UTC)
            }
        ]
        
        # Crear usuarios
        for usuario_data in usuarios_prueba:
            db_usuario = Usuario(**usuario_data)
            db.add(db_usuario)
        
        db.commit()
        print("Usuarios de prueba creados exitosamente:")
        print("1. Admin - username: admin, password: admin123")
        print("2. Camarero - username: camarero, password: camarero123")
        print("3. Cocinero - username: cocinero, password: cocinero123")
    
    except Exception as e:
        db.rollback()
        print(f"Error al crear usuarios de prueba: {str(e)}")
    
    finally:
        db.close()

if __name__ == "__main__":
    crear_usuarios_prueba() 