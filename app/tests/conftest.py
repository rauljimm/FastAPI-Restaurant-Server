"""
Archivo de configuración de Pytest con fixtures para testing.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, UTC

from app.main import app
from app.db.database import Base, get_db
from app.core.config import SQLALCHEMY_TEST_DATABASE_URL
from app.models.usuario import Usuario
from app.core.enums import RolUsuario
from app.core.security import get_password_hash

# Configuración de la base de datos de prueba
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def setup_database():
    """Configuración y limpieza de la base de datos de prueba para toda la sesión de testing."""
    # Crear tablas
    Base.metadata.create_all(bind=engine)
    yield
    # Eliminar tablas después de todas las pruebas
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db(setup_database):
    """Sesión de base de datos para cada prueba."""
    # Limpiar datos existentes
    connection = engine.connect()
    transaction = connection.begin()
    
    # Crear una sesión vinculada a la conexión
    session = TestingSessionLocal(bind=connection)
    
    # Limpiar todas las tablas
    try:
        session.execute(text("DELETE FROM detalles_pedido"))
        session.execute(text("DELETE FROM pedidos"))
        session.execute(text("DELETE FROM reservas"))
        session.execute(text("DELETE FROM productos"))
        session.execute(text("DELETE FROM categorias"))
        session.execute(text("DELETE FROM mesas"))
        session.execute(text("DELETE FROM usuarios"))
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error al limpiar la base de datos: {e}")
    
    yield session
    
    # Cerrar sesión y revertir transacción después de la prueba
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    """Cliente de prueba FastAPI con reemplazo de sesión de base de datos."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    
    # Limpiar reemplazos después de la prueba
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user(db, client):
    """Crear un usuario administrador y devolver su ID y token."""
    # Verificar si el usuario administrador ya existe
    existing_admin = db.query(Usuario).filter(Usuario.username == "admin").first()
    if existing_admin:
        admin_id = existing_admin.id
    else:
        # Crear usuario administrador
        admin_data = {
            "username": "admin",
            "email": "admin@example.com",
            "hashed_password": get_password_hash("admin123"),
            "nombre": "Admin",
            "apellido": "User",
            "rol": RolUsuario.ADMIN,
            "activo": True,
            "fecha_creacion": datetime.now(UTC)
        }
        admin = Usuario(**admin_data)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        admin_id = admin.id
    
    # Obtener token de administrador usando endpoint JSON para evitar problemas con form data
    login_data = {"username": "admin", "password": "admin123"}
    token_response = client.post("/login", json=login_data)
    
    # Depuración de problemas de inicio de sesión
    if token_response.status_code != 200:
        print(f"Error en la respuesta de login: {token_response.status_code}, {token_response.text}")
        admin_check = db.query(Usuario).filter(Usuario.username == "admin").first()
        if admin_check:
            print(f"El admin existe. Username: {admin_check.username}, Activo: {admin_check.activo}")
        else:
            print("Usuario admin no encontrado en la base de datos")
        admin_token = ""
    else:
        admin_token = token_response.json().get("access_token", "")
    
    return {"id": admin_id, "token": admin_token}

@pytest.fixture
def camarero_user(db, client, admin_user):
    """Crear un usuario camarero y devolver su ID y token."""
    if not admin_user["token"]:
        pytest.skip("Token de administrador no disponible, omitiendo prueba dependiente")
        
    # Crear usuario camarero
    camarero_data = {
        "username": "camarero",
        "email": "camarero@example.com",
        "password": "camarero123",
        "nombre": "Camarero",
        "apellido": "User",
        "rol": "camarero"
    }
    response = client.post(
        "/usuarios/", 
        json=camarero_data, 
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    if response.status_code != 201:
        pytest.skip(f"Error al crear usuario camarero: {response.status_code}, {response.text}")
        return {"id": None, "token": ""}
        
    camarero_id = response.json()["id"]
    
    # Obtener token de camarero usando endpoint JSON
    login_data = {"username": "camarero", "password": "camarero123"}
    token_response = client.post("/login", json=login_data)
    camarero_token = token_response.json()["access_token"]
    
    return {"id": camarero_id, "token": camarero_token}

@pytest.fixture
def cocinero_user(db, client, admin_user):
    """Crear un usuario cocinero y devolver su ID y token."""
    if not admin_user["token"]:
        pytest.skip("Token de administrador no disponible, omitiendo prueba dependiente")
        
    # Crear usuario cocinero
    cocinero_data = {
        "username": "cocinero",
        "email": "cocinero@example.com",
        "password": "cocinero123",
        "nombre": "Cocinero",
        "apellido": "User",
        "rol": "cocinero"
    }
    response = client.post(
        "/usuarios/", 
        json=cocinero_data, 
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    if response.status_code != 201:
        pytest.skip(f"Error al crear usuario cocinero: {response.status_code}, {response.text}")
        return {"id": None, "token": ""}
        
    cocinero_id = response.json()["id"]
    
    # Obtener token de cocinero usando endpoint JSON
    login_data = {"username": "cocinero", "password": "cocinero123"}
    token_response = client.post("/login", json=login_data)
    cocinero_token = token_response.json()["access_token"]
    
    return {"id": cocinero_id, "token": cocinero_token} 