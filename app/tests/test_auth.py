"""
Tests para los endpoints de autenticación.
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
    """Crear un usuario administrador específicamente para la prueba de login."""
    # Verificar si admin ya existe
    existing = db.query(Usuario).filter(Usuario.username == "admin").first()
    if existing:
        db.delete(existing)
        db.commit()
    
    # Crear un nuevo usuario admin con contraseña conocida
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
        """Probar inicio de sesión exitoso con JSON."""
        response = client.post("/login", json={"username": "admin", "password": "admin123"})
        # Imprimir detalles de la respuesta para depuración
        print(f"Respuesta de login: status={response.status_code}, body={response.text}")
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client, admin_user):
        """Probar inicio de sesión con credenciales inválidas usando JSON."""
        # Contraseña incorrecta
        response = client.post("/login", json={"username": "admin", "password": "wrong_password"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Usuario inexistente
        response = client.post("/login", json={"username": "nonexistent", "password": "password"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token(self, client):
        """Probar acceso a un endpoint protegido con token inválido."""
        response = client.get(
            "/usuarios/me", 
            headers={"Authorization": f"Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_current_user(self, client, admin_user):
        """Probar obtención de la información del usuario actual."""
        if not admin_user["token"]:
            pytest.skip("Token de administrador no disponible, omitiendo prueba")
            
        response = client.get(
            "/usuarios/me", 
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "admin" 