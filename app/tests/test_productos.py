"""
Tests para los endpoints de gestión de productos.
"""
import pytest
from fastapi import status
from app.core.enums import TipoProducto

@pytest.fixture
def categoria(client, admin_user):
    """Crear una categoría de prueba y devolver sus datos."""
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
    """Crear un producto de prueba y devolver sus datos."""
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
        """Probar la creación de un nuevo producto."""
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
        """Probar la creación de un producto con una categoría inexistente."""
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
        """Probar que los usuarios no administradores no pueden crear productos."""
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
        """Probar la obtención de todos los productos."""
        # Petición de admin
        response = client.get(
            "/productos/",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Petición de camarero
        response = client.get(
            "/productos/",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Probar con filtros
        response = client.get(
            f"/productos/?categoria_id={producto['categoria_id']}&tipo={producto['tipo']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        assert response.json()[0]["categoria_id"] == producto["categoria_id"]
        
        # Probar con filtro de disponibilidad
        response = client.get(
            "/productos/?disponible=true",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert all(p["disponible"] for p in response.json())

    def test_get_producto_by_id(self, client, admin_user, producto):
        """Probar la obtención de un producto específico por ID."""
        response = client.get(
            f"/productos/{producto['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == producto["id"]
        assert response.json()["nombre"] == producto["nombre"]
        assert "categoria" in response.json()  # Verificar que devuelve el producto detallado con información de categoría

    def test_update_producto(self, client, admin_user, producto):
        """Probar la actualización de un producto."""
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
        """Probar que los usuarios no administradores no pueden actualizar productos."""
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
        """Probar la eliminación de un producto."""
        # Crear un producto para eliminar
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
        
        # Eliminar el producto
        response = client.delete(
            f"/productos/{producto_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que el producto ha sido eliminado
        get_response = client.get(
            f"/productos/{producto_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_producto_unauthorized(self, client, camarero_user, producto):
        """Probar que los usuarios no administradores no pueden eliminar productos."""
        response = client.delete(
            f"/productos/{producto['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN 