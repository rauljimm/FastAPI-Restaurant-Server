"""
Tests for authentication endpoints.
"""
import pytest
from fastapi import status
from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.core.enums import RolUsuario
from app.core.security import get_password_hash
from datetime import datetime, UTC

@pytest.fixture
def setup_admin_user(db: Session):
    """Create an admin user specifically for login test."""
    # Check if admin already exists
    existing = db.query(Usuario).filter(Usuario.username == "admin").first()
    if existing:
        db.delete(existing)
        db.commit()
    
    # Create fresh admin user with known password
    admin_user = Usuario(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        nombre="Admin",
        apellido="User",
        rol=RolUsuario.ADMIN,
        activo=True,
        fecha_creacion=datetime.now(UTC)
    )
    db.add(admin_user)
    db.commit()
    return admin_user

class TestAuthentication:
    def test_login_success(self, client, setup_admin_user):
        """Test successful login."""
        response = client.post("/token", data={"username": "admin", "password": "admin123"})
        # Print response details for debugging
        print(f"Login response: status={response.status_code}, body={response.text}")
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client, admin_user):
        """Test login with invalid credentials."""
        # Wrong password
        response = client.post("/token", data={"username": "admin", "password": "wrong_password"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Non-existent user
        response = client.post("/token", data={"username": "nonexistent", "password": "password"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token(self, client):
        """Test accessing a protected endpoint with invalid token."""
        response = client.get(
            "/usuarios/me", 
            headers={"Authorization": f"Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_current_user(self, client, admin_user):
        """Test getting the current user's information."""
        response = client.get(
            "/usuarios/me", 
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "admin" 