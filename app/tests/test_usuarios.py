"""
Tests para los endpoints de gestión de usuarios.
"""
import pytest
from fastapi import status

class TestUsuarios:
    def test_create_usuario(self, client, admin_user):
        """Probar la creación de un nuevo usuario."""
        if not admin_user["token"]:
            pytest.skip("Token de administrador no disponible, omitiendo prueba")
            
        # Crear un nuevo usuario como admin
        new_user = {
            "username": "nuevo",
            "email": "nuevo@example.com",
            "password": "nuevo123",
            "nombre": "Nuevo",
            "apellido": "User",
            "rol": "camarero"
        }
        response = client.post(
            "/usuarios/",
            json=new_user,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["username"] == "nuevo"
        assert "id" in response.json()

    def test_create_duplicate_usuario(self, client, admin_user):
        """Probar la creación de un usuario con username duplicado."""
        if not admin_user["token"]:
            pytest.skip("Token de administrador no disponible, omitiendo prueba")
            
        # Crear un usuario
        user_data = {
            "username": "duplicate",
            "email": "duplicate@example.com",
            "password": "duplicate123",
            "nombre": "Duplicate",
            "apellido": "User",
            "rol": "camarero"
        }
        create_response = client.post(
            "/usuarios/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert create_response.status_code == status.HTTP_201_CREATED, f"Error al crear el primer usuario: {create_response.text}"
        
        # Intentar crear el mismo usuario nuevamente
        response = client.post(
            "/usuarios/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_usuario_unauthorized(self, client, camarero_user):
        """Probar que los usuarios no administradores no pueden crear usuarios."""
        if not camarero_user["token"]:
            pytest.skip("Token de camarero no disponible, omitiendo prueba")
            
        new_user = {
            "username": "another",
            "email": "another@example.com",
            "password": "another123",
            "nombre": "Another",
            "apellido": "User",
            "rol": "camarero"
        }
        response = client.post(
            "/usuarios/",
            json=new_user,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_usuarios(self, client, admin_user, camarero_user, cocinero_user):
        """Probar la obtención de todos los usuarios."""
        if not admin_user["token"]:
            pytest.skip("Token de administrador no disponible, omitiendo prueba")
            
        response = client.get(
            "/usuarios/",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1  # Al menos el admin

    def test_get_usuario_by_id(self, client, admin_user):
        """Probar la obtención de un usuario específico por ID."""
        if not admin_user["token"]:
            pytest.skip("Token de administrador no disponible, omitiendo prueba")
            
        response = client.get(
            f"/usuarios/{admin_user['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == admin_user['id']
        assert response.json()["username"] == "admin"

    def test_get_usuario_unauthorized(self, client, admin_user, camarero_user):
        """Probar que los usuarios solo pueden ver su propio perfil."""
        if not camarero_user["token"] or not admin_user["id"]:
            pytest.skip("Tokens o IDs necesarios no disponibles, omitiendo prueba")
            
        # Camarero intentando ver el perfil del admin
        response = client.get(
            f"/usuarios/{admin_user['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_own_usuario(self, client, camarero_user):
        """Probar que un usuario puede actualizar su propio perfil."""
        if not camarero_user["token"] or not camarero_user["id"]:
            pytest.skip("Token o ID de camarero no disponible, omitiendo prueba")
            
        update_data = {
            "nombre": "Updated",
            "apellido": "Name"
        }
        response = client.put(
            f"/usuarios/{camarero_user['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["nombre"] == "Updated"
        assert response.json()["apellido"] == "Name"

    def test_update_other_usuario(self, client, admin_user, camarero_user):
        """Probar que admin puede actualizar otros usuarios pero no-admin no puede."""
        if not admin_user["token"] or not camarero_user["token"] or not camarero_user["id"] or not admin_user["id"]:
            pytest.skip("Tokens o IDs necesarios no disponibles, omitiendo prueba")
            
        update_data = {
            "nombre": "AdminUpdated"
        }
        
        # Admin actualizando camarero
        response = client.put(
            f"/usuarios/{camarero_user['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["nombre"] == "AdminUpdated"
        
        # Camarero intentando actualizar admin
        response = client.put(
            f"/usuarios/{admin_user['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_usuario(self, client, admin_user):
        """Probar la eliminación de un usuario."""
        if not admin_user["token"]:
            pytest.skip("Token de administrador no disponible, omitiendo prueba")
            
        # Crear un usuario para eliminar
        new_user = {
            "username": "to_delete",
            "email": "delete@example.com",
            "password": "delete123",
            "nombre": "Delete",
            "apellido": "User",
            "rol": "camarero"
        }
        create_response = client.post(
            "/usuarios/",
            json=new_user,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert create_response.status_code == status.HTTP_201_CREATED, f"Error al crear usuario: {create_response.text}"
        user_id = create_response.json()["id"]
        
        # Eliminar el usuario
        response = client.delete(
            f"/usuarios/{user_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que el usuario ha sido eliminado
        get_response = client.get(
            f"/usuarios/{user_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_last_admin(self, client, admin_user):
        """Probar que el último administrador no puede ser eliminado."""
        if not admin_user["token"] or not admin_user["id"]:
            pytest.skip("Token o ID de administrador no disponible, omitiendo prueba")
            
        response = client.delete(
            f"/usuarios/{admin_user['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST 