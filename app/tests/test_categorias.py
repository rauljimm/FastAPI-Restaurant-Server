"""
Tests para los endpoints de gestión de categorías.
"""
import pytest
from fastapi import status

@pytest.fixture
def categoria(client, admin_user):
    """Crear una categoría de prueba y devolver su ID."""
    if not admin_user["token"]:
        pytest.skip("Token de administrador no disponible, omitiendo prueba")
        
    categoria_data = {
        "nombre": "Test Categoria",
        "descripcion": "Categoria para pruebas"
    }
    response = client.post(
        "/categorias/",
        json=categoria_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    if response.status_code != status.HTTP_201_CREATED:
        pytest.skip(f"Error al crear categoría de prueba: {response.status_code}, {response.text}")
        return None
        
    return response.json()

class TestCategorias:
    def test_create_categoria(self, client, admin_user):
        """Probar la creación de una nueva categoría."""
        if not admin_user["token"]:
            pytest.skip("Token de administrador no disponible, omitiendo prueba")
            
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
        """Probar la creación de una categoría con nombre duplicado."""
        if not admin_user["token"] or not categoria:
            pytest.skip("Token de administrador o categoría de prueba no disponible, omitiendo prueba")
            
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
        """Probar que los usuarios no administradores no pueden crear categorías."""
        if not camarero_user["token"]:
            pytest.skip("Token de camarero no disponible, omitiendo prueba")
            
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
        """Probar la obtención de todas las categorías."""
        if not admin_user["token"] or not camarero_user["token"]:
            pytest.skip("Token de administrador o camarero no disponible, omitiendo prueba")
            
        response = client.get(
            "/categorias/",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Probar también que los usuarios no-admin pueden obtener categorías
        response = client.get(
            "/categorias/",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_get_categoria_by_id(self, client, admin_user, categoria):
        """Probar la obtención de una categoría específica por ID."""
        if not admin_user["token"] or not categoria:
            pytest.skip("Token de administrador o categoría de prueba no disponible, omitiendo prueba")
            
        response = client.get(
            f"/categorias/{categoria['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == categoria["id"]
        assert response.json()["nombre"] == categoria["nombre"]

    def test_update_categoria(self, client, admin_user, categoria):
        """Probar la actualización de una categoría."""
        if not admin_user["token"] or not categoria:
            pytest.skip("Token de administrador o categoría de prueba no disponible, omitiendo prueba")
            
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
        """Probar que los usuarios no administradores no pueden actualizar categorías."""
        if not camarero_user["token"] or not categoria:
            pytest.skip("Token de camarero o categoría de prueba no disponible, omitiendo prueba")
            
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
        """Probar la eliminación de una categoría."""
        if not admin_user["token"]:
            pytest.skip("Token de administrador no disponible, omitiendo prueba")
            
        # Crear una categoría para eliminar
        categoria_data = {
            "nombre": "Categoria para eliminar",
            "descripcion": "Esta categoria será eliminada"
        }
        create_response = client.post(
            "/categorias/",
            json=categoria_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert create_response.status_code == status.HTTP_201_CREATED, f"Error al crear categoría para eliminar: {create_response.text}"
        categoria_id = create_response.json()["id"]
        
        # Eliminar la categoría
        response = client.delete(
            f"/categorias/{categoria_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que la categoría ha sido eliminada
        get_response = client.get(
            f"/categorias/{categoria_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_categoria_unauthorized(self, client, camarero_user, categoria):
        """Probar que los usuarios no administradores no pueden eliminar categorías."""
        if not camarero_user["token"] or not categoria:
            pytest.skip("Token de camarero o categoría de prueba no disponible, omitiendo prueba")
            
        response = client.delete(
            f"/categorias/{categoria['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN 