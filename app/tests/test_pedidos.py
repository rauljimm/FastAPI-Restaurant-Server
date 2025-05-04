"""
Tests for order management endpoints.
"""
import pytest
from fastapi import status
from app.core.enums import EstadoPedido, TipoProducto

@pytest.fixture
def mesa(client, admin_user):
    """Create a test table and return its data."""
    mesa_data = {
        "numero": 10,
        "capacidad": 4,
        "ubicacion": "Interior"
    }
    response = client.post(
        "/mesas/",
        json=mesa_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

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

@pytest.fixture
def pedido(client, camarero_user, mesa, producto):
    """Create a test order and return its data."""
    pedido_data = {
        "mesa_id": mesa["id"],
        "observaciones": "Pedido de prueba",
        "detalles": [
            {
                "producto_id": producto["id"],
                "cantidad": 2,
                "observaciones": "Sin sal"
            }
        ]
    }
    response = client.post(
        "/pedidos/",
        json=pedido_data,
        headers={"Authorization": f"Bearer {camarero_user['token']}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

class TestPedidos:
    def test_create_pedido(self, client, camarero_user, mesa, producto):
        """Test creating a new order."""
        pedido_data = {
            "mesa_id": mesa["id"],
            "observaciones": "Nuevo pedido",
            "detalles": [
                {
                    "producto_id": producto["id"],
                    "cantidad": 1,
                    "observaciones": "Observación detalle"
                }
            ]
        }
        response = client.post(
            "/pedidos/",
            json=pedido_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["mesa_id"] == mesa["id"]
        assert response.json()["observaciones"] == "Nuevo pedido"
        assert response.json()["estado"] == EstadoPedido.RECIBIDO
        assert len(response.json()["detalles"]) == 1
        assert response.json()["detalles"][0]["cantidad"] == 1
        assert response.json()["detalles"][0]["producto_id"] == producto["id"]
        assert "id" in response.json()

    def test_create_pedido_mesa_inexistente(self, client, camarero_user, producto):
        """Test creating an order with a non-existent table."""
        pedido_data = {
            "mesa_id": 999999,  # ID no existente
            "detalles": [
                {
                    "producto_id": producto["id"],
                    "cantidad": 1
                }
            ]
        }
        response = client.post(
            "/pedidos/",
            json=pedido_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_pedido_producto_inexistente(self, client, camarero_user, mesa):
        """Test creating an order with a non-existent product."""
        pedido_data = {
            "mesa_id": mesa["id"],
            "detalles": [
                {
                    "producto_id": 999999,  # ID no existente
                    "cantidad": 1
                }
            ]
        }
        response = client.post(
            "/pedidos/",
            json=pedido_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_pedido_unauthorized(self, client, cocinero_user, mesa, producto):
        """Test that cooks cannot create orders."""
        pedido_data = {
            "mesa_id": mesa["id"],
            "detalles": [
                {
                    "producto_id": producto["id"],
                    "cantidad": 1
                }
            ]
        }
        response = client.post(
            "/pedidos/",
            json=pedido_data,
            headers={"Authorization": f"Bearer {cocinero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_pedidos(self, client, admin_user, camarero_user, cocinero_user, pedido):
        """Test getting orders with different user roles."""
        # Admin request (can see all orders)
        response = client.get(
            "/pedidos/",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Camarero request (can see own orders)
        response = client.get(
            "/pedidos/",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Cocinero request (can see all orders)
        response = client.get(
            "/pedidos/",
            headers={"Authorization": f"Bearer {cocinero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Test with filters
        response = client.get(
            f"/pedidos/?estado=recibido&mesa_id={pedido['mesa_id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        assert all(p["estado"] == EstadoPedido.RECIBIDO for p in response.json())
        assert all(p["mesa_id"] == pedido["mesa_id"] for p in response.json())

    def test_get_pedido_by_id(self, client, admin_user, camarero_user, cocinero_user, pedido):
        """Test getting a specific order by ID."""
        # Admin request
        response = client.get(
            f"/pedidos/{pedido['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == pedido["id"]
        assert "detalles" in response.json()
        
        # Camarero request
        response = client.get(
            f"/pedidos/{pedido['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Cocinero request
        response = client.get(
            f"/pedidos/{pedido['id']}",
            headers={"Authorization": f"Bearer {cocinero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_pedido(self, client, camarero_user, cocinero_user, pedido):
        """Test updating an order status by different users."""
        # Camarero updating observaciones
        update_data = {
            "observaciones": "Actualizado por camarero"
        }
        response = client.put(
            f"/pedidos/{pedido['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["observaciones"] == "Actualizado por camarero"
        
        # Cocinero updating to EN_PREPARACION
        update_data = {
            "estado": EstadoPedido.EN_PREPARACION
        }
        response = client.put(
            f"/pedidos/{pedido['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {cocinero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["estado"] == EstadoPedido.EN_PREPARACION
        
        # Cocinero updating to LISTO
        update_data = {
            "estado": EstadoPedido.LISTO
        }
        response = client.put(
            f"/pedidos/{pedido['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {cocinero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["estado"] == EstadoPedido.LISTO
        
        # Camarero updating to ENTREGADO
        update_data = {
            "estado": EstadoPedido.ENTREGADO
        }
        response = client.put(
            f"/pedidos/{pedido['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["estado"] == EstadoPedido.ENTREGADO

    def test_update_pedido_cocinero_limitado(self, client, cocinero_user, pedido):
        """Test cook can only update to specific states."""
        # Cocinero trying to update to ENTREGADO (not allowed)
        update_data = {
            "estado": EstadoPedido.ENTREGADO
        }
        response = client.put(
            f"/pedidos/{pedido['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {cocinero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_add_detalle_pedido(self, client, camarero_user, pedido, producto):
        """Test adding a new item to an existing order."""
        detalle_data = {
            "producto_id": producto["id"],
            "cantidad": 3,
            "observaciones": "Detalle añadido después"
        }
        response = client.post(
            f"/pedidos/{pedido['id']}/detalles/",
            json=detalle_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["producto_id"] == producto["id"]
        assert response.json()["cantidad"] == 3
        assert response.json()["observaciones"] == "Detalle añadido después"

    def test_update_detalle_pedido(self, client, camarero_user, cocinero_user, pedido):
        """Test updating an order detail."""
        # Get detail ID
        detalle_id = pedido["detalles"][0]["id"]
        
        # Camarero updating quantity
        update_data = {
            "cantidad": 5
        }
        response = client.put(
            f"/pedidos/{pedido['id']}/detalles/{detalle_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["cantidad"] == 5
        
        # Cocinero updating status
        update_data = {
            "estado": EstadoPedido.EN_PREPARACION
        }
        response = client.put(
            f"/pedidos/{pedido['id']}/detalles/{detalle_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {cocinero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["estado"] == EstadoPedido.EN_PREPARACION

    def test_delete_detalle_pedido(self, client, camarero_user, pedido, producto):
        """Test deleting an item from an order and adding a new one first."""
        # Add another detail to delete
        detalle_data = {
            "producto_id": producto["id"],
            "cantidad": 1,
            "observaciones": "Para eliminar"
        }
        add_response = client.post(
            f"/pedidos/{pedido['id']}/detalles/",
            json=detalle_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        detalle_id = add_response.json()["id"]
        
        # Delete the detail
        response = client.delete(
            f"/pedidos/{pedido['id']}/detalles/{detalle_id}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify the detail is deleted
        get_response = client.get(
            f"/pedidos/{pedido['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        detalle_ids = [d["id"] for d in get_response.json()["detalles"]]
        assert detalle_id not in detalle_ids 