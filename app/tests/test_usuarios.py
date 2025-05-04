"""
Tests for user management endpoints.
"""
import pytest
from fastapi import status

class TestUsuarios:
    def test_create_usuario(self, client, admin_user):
        """Test creating a new user."""
        # Create a new user as admin
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
        """Test creating a user with duplicate username."""
        # Create a user
        user_data = {
            "username": "duplicate",
            "email": "duplicate@example.com",
            "password": "duplicate123",
            "nombre": "Duplicate",
            "apellido": "User",
            "rol": "camarero"
        }
        client.post(
            "/usuarios/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        
        # Try to create the same user again
        response = client.post(
            "/usuarios/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_usuario_unauthorized(self, client, camarero_user):
        """Test that non-admin users cannot create users."""
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
        """Test getting all users."""
        response = client.get(
            "/usuarios/",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 3  # admin, camarero, cocinero

    def test_get_usuario_by_id(self, client, admin_user):
        """Test getting a specific user by ID."""
        response = client.get(
            f"/usuarios/{admin_user['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == admin_user['id']
        assert response.json()["username"] == "admin"

    def test_get_usuario_unauthorized(self, client, admin_user, camarero_user):
        """Test that users can only view their own profile."""
        # Camarero trying to view admin's profile
        response = client.get(
            f"/usuarios/{admin_user['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_own_usuario(self, client, camarero_user):
        """Test that a user can update their own profile."""
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
        """Test that admin can update other users but non-admin cannot."""
        update_data = {
            "nombre": "AdminUpdated"
        }
        
        # Admin updating camarero
        response = client.put(
            f"/usuarios/{camarero_user['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["nombre"] == "AdminUpdated"
        
        # Camarero trying to update admin
        response = client.put(
            f"/usuarios/{admin_user['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_usuario(self, client, admin_user):
        """Test deleting a user."""
        # Create a user to delete
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
        user_id = create_response.json()["id"]
        
        # Delete the user
        response = client.delete(
            f"/usuarios/{user_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify user is deleted
        get_response = client.get(
            f"/usuarios/{user_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_last_admin(self, client, admin_user):
        """Test that the last admin cannot be deleted."""
        response = client.delete(
            f"/usuarios/{admin_user['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST 