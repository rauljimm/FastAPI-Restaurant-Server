"""
Tests for product management endpoints.
"""
import pytest
from fastapi import status
from app.core.enums import TipoProducto

@pytest.fixture
def categoria(client, admin_user):
    """Create a test category and return its data."""
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

@pytest.fixture
def producto(client, admin_user, categoria):
    """Create a test product and return its data."""
    producto_data = {
        "nombre": "Test Producto",
        "descripcion": "Producto para pruebas",
        "precio": 9.99,
        "tiempo_preparacion": 15,
        "categoria_id": categoria["id"],
        "tipo": TipoProducto.COMIDA,
        "disponible": True
    }
    response = client.post(
        "/productos/",
        json=producto_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

class TestProductos:
    def test_create_producto(self, client, admin_user, categoria):
        """Test creating a new product."""
        producto_data = {
            "nombre": "Nuevo Producto",
            "descripcion": "Un producto de prueba",
            "precio": 14.99,
            "tiempo_preparacion": 10,
            "categoria_id": categoria["id"],
            "tipo": TipoProducto.BEBIDA,
            "disponible": True
        }
        response = client.post(
            "/productos/",
            json=producto_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["nombre"] == "Nuevo Producto"
        assert response.json()["precio"] == 14.99
        assert response.json()["tipo"] == TipoProducto.BEBIDA
        assert "id" in response.json()

    def test_create_producto_categoria_inexistente(self, client, admin_user):
        """Test creating a product with a non-existent category."""
        producto_data = {
            "nombre": "Producto Invalido",
            "precio": 12.99,
            "tiempo_preparacion": 5,
            "categoria_id": 999999,  # ID no existente
            "tipo": TipoProducto.COMIDA,
            "disponible": True
        }
        response = client.post(
            "/productos/",
            json=producto_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_producto_unauthorized(self, client, camarero_user, categoria):
        """Test that non-admin users cannot create products."""
        producto_data = {
            "nombre": "Producto No Autorizado",
            "precio": 7.99,
            "tiempo_preparacion": 5,
            "categoria_id": categoria["id"],
            "tipo": TipoProducto.POSTRE,
            "disponible": True
        }
        response = client.post(
            "/productos/",
            json=producto_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_productos(self, client, admin_user, camarero_user, producto):
        """Test getting all products."""
        # Admin request
        response = client.get(
            "/productos/",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Camarero request
        response = client.get(
            "/productos/",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Test with filters
        response = client.get(
            f"/productos/?categoria_id={producto['categoria_id']}&tipo={producto['tipo']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        assert response.json()[0]["categoria_id"] == producto["categoria_id"]
        
        # Test with disponible filter
        response = client.get(
            "/productos/?disponible=true",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert all(p["disponible"] for p in response.json())

    def test_get_producto_by_id(self, client, admin_user, producto):
        """Test getting a specific product by ID."""
        response = client.get(
            f"/productos/{producto['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == producto["id"]
        assert response.json()["nombre"] == producto["nombre"]
        assert "categoria" in response.json()  # Check that it returns the detailed product with category info

    def test_update_producto(self, client, admin_user, producto):
        """Test updating a product."""
        update_data = {
            "nombre": "Producto Actualizado",
            "precio": 19.99,
            "disponible": False
        }
        response = client.put(
            f"/productos/{producto['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["nombre"] == "Producto Actualizado"
        assert response.json()["precio"] == 19.99
        assert response.json()["disponible"] == False

    def test_update_producto_unauthorized(self, client, camarero_user, producto):
        """Test that non-admin users cannot update products."""
        update_data = {
            "nombre": "Intento No Autorizado"
        }
        response = client.put(
            f"/productos/{producto['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_producto(self, client, admin_user, categoria):
        """Test deleting a product."""
        # Create a product to delete
        producto_data = {
            "nombre": "Producto para eliminar",
            "precio": 5.99,
            "tiempo_preparacion": 5,
            "categoria_id": categoria["id"],
            "tipo": TipoProducto.COMPLEMENTO,
            "disponible": True
        }
        create_response = client.post(
            "/productos/",
            json=producto_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        producto_id = create_response.json()["id"]
        
        # Delete the product
        response = client.delete(
            f"/productos/{producto_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify the product is deleted
        get_response = client.get(
            f"/productos/{producto_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_producto_unauthorized(self, client, camarero_user, producto):
        """Test that non-admin users cannot delete products."""
        response = client.delete(
            f"/productos/{producto['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN 