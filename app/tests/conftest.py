"""
Pytest configuration file with fixtures for testing.
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

# Setup test database
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def setup_database():
    """Setup and teardown of the test database for the entire test session."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after all tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db(setup_database):
    """Database session for each test."""
    # Clear existing data
    connection = engine.connect()
    transaction = connection.begin()
    
    # Create a session bound to the connection
    session = TestingSessionLocal(bind=connection)
    
    # Clear all tables
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
        print(f"Error clearing database: {e}")
    
    yield session
    
    # Close session and rollback transaction after test
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    """FastAPI test client with database session override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear overrides after test
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user(db):
    """Create an admin user and return its ID and token."""
    # Create admin user
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
    
    # Get admin token 
    with TestClient(app) as client:
        token_data = {"username": "admin", "password": "admin123"}
        token_response = client.post("/token", data=token_data)
        # Debug password verification issues
        if token_response.status_code != 200:
            print(f"Token response failed: {token_response.status_code}, {token_response.text}")
            # Try to retrieve the user to confirm it exists
            admin_check = db.query(Usuario).filter(Usuario.username == "admin").first()
            if admin_check:
                print(f"Admin exists. Username: {admin_check.username}, Active: {admin_check.activo}")
            else:
                print("Admin user not found in database")
        admin_token = token_response.json().get("access_token", "")
    
    return {"id": admin.id, "token": admin_token}

@pytest.fixture
def camarero_user(db, client, admin_user):
    """Create a waiter user and return its ID and token."""
    # Create waiter user
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
    camarero_id = response.json()["id"]
    
    # Get waiter token
    token_response = client.post("/token", data={"username": "camarero", "password": "camarero123"})
    camarero_token = token_response.json()["access_token"]
    
    return {"id": camarero_id, "token": camarero_token}

@pytest.fixture
def cocinero_user(db, client, admin_user):
    """Create a cook user and return its ID and token."""
    # Create cook user
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
    cocinero_id = response.json()["id"]
    
    # Get cook token
    token_response = client.post("/token", data={"username": "cocinero", "password": "cocinero123"})
    cocinero_token = token_response.json()["access_token"]
    
    return {"id": cocinero_id, "token": cocinero_token} 