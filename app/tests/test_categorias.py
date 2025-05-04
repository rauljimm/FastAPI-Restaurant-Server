"""
Tests for category management endpoints.
"""
import pytest
from fastapi import status

@pytest.fixture
def categoria(client, admin_user):
    """Create a test category and return its ID."""
    categoria_data = {
        "nombre": "Test Categoria",
        "descripcion": "Categoria para pruebas"
    }
    response = client.post(
        "/categorias/",
        json=categoria_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

class TestCategorias:
    def test_create_categoria(self, client, admin_user):
        """Test creating a new category."""
        categoria_data = {
            "nombre": "Nueva Categoria",
            "descripcion": "Una categoria de prueba"
        }
        response = client.post(
            "/categorias/",
            json=categoria_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["nombre"] == "Nueva Categoria"
        assert response.json()["descripcion"] == "Una categoria de prueba"
        assert "id" in response.json()

    def test_create_categoria_duplicate(self, client, admin_user, categoria):
        """Test creating a category with a duplicate name."""
        categoria_data = {
            "nombre": categoria["nombre"],
            "descripcion": "Otra descripcion"
        }
        response = client.post(
            "/categorias/",
            json=categoria_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_categoria_unauthorized(self, client, camarero_user):
        """Test that non-admin users cannot create categories."""
        categoria_data = {
            "nombre": "Categoria No Autorizada",
            "descripcion": "Esta no debería crearse"
        }
        response = client.post(
            "/categorias/",
            json=categoria_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_categorias(self, client, admin_user, camarero_user, categoria):
        """Test getting all categories."""
        response = client.get(
            "/categorias/",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Also test that non-admin users can get categories
        response = client.get(
            "/categorias/",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_get_categoria_by_id(self, client, admin_user, categoria):
        """Test getting a specific category by ID."""
        response = client.get(
            f"/categorias/{categoria['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == categoria["id"]
        assert response.json()["nombre"] == categoria["nombre"]

    def test_update_categoria(self, client, admin_user, categoria):
        """Test updating a category."""
        update_data = {
            "nombre": "Categoria Actualizada",
            "descripcion": "Descripcion actualizada"
        }
        response = client.put(
            f"/categorias/{categoria['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["nombre"] == "Categoria Actualizada"
        assert response.json()["descripcion"] == "Descripcion actualizada"

    def test_update_categoria_unauthorized(self, client, camarero_user, categoria):
        """Test that non-admin users cannot update categories."""
        update_data = {
            "nombre": "Intento no autorizado"
        }
        response = client.put(
            f"/categorias/{categoria['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_categoria(self, client, admin_user):
        """Test deleting a category."""
        # Create a category to delete
        categoria_data = {
            "nombre": "Categoria para eliminar",
            "descripcion": "Esta categoria será eliminada"
        }
        create_response = client.post(
            "/categorias/",
            json=categoria_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        categoria_id = create_response.json()["id"]
        
        # Delete the category
        response = client.delete(
            f"/categorias/{categoria_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify the category is deleted
        get_response = client.get(
            f"/categorias/{categoria_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_categoria_unauthorized(self, client, camarero_user, categoria):
        """Test that non-admin users cannot delete categories."""
        response = client.delete(
            f"/categorias/{categoria['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN 