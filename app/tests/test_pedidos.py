"""
Tests para los endpoints de gestión de pedidos.
"""
import pytest
from fastapi import status
from app.core.enums import EstadoPedido, TipoProducto

@pytest.fixture
def mesa(client, admin_user):
    """Crear una mesa de prueba y devolver sus datos."""
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

@pytest.fixture
def pedido(client, camarero_user, mesa, producto):
    """Crear un pedido de prueba y devolver sus datos."""
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
        """Probar la creación de un nuevo pedido."""
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
        """Probar la creación de un pedido con una mesa inexistente."""
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
        """Probar la creación de un pedido con un producto inexistente."""
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
        """Probar que los cocineros no pueden crear pedidos."""
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
        """Probar la obtención de pedidos con diferentes roles de usuario."""
        # Petición de admin (puede ver todos los pedidos)
        response = client.get(
            "/pedidos/",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Petición de camarero (puede ver sus propios pedidos)
        response = client.get(
            "/pedidos/",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Petición de cocinero (puede ver todos los pedidos)
        response = client.get(
            "/pedidos/",
            headers={"Authorization": f"Bearer {cocinero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Probar con filtros
        response = client.get(
            f"/pedidos/?estado=recibido&mesa_id={pedido['mesa_id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        assert all(p["estado"] == EstadoPedido.RECIBIDO for p in response.json())
        assert all(p["mesa_id"] == pedido["mesa_id"] for p in response.json())

    def test_get_pedido_by_id(self, client, admin_user, camarero_user, cocinero_user, pedido):
        """Probar la obtención de un pedido específico por ID."""
        # Admin puede ver cualquier pedido
        response = client.get(
            f"/pedidos/{pedido['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == pedido["id"]
        
        # Camarero puede ver su propio pedido
        response = client.get(
            f"/pedidos/{pedido['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Cocinero puede ver cualquier pedido
        response = client.get(
            f"/pedidos/{pedido['id']}",
            headers={"Authorization": f"Bearer {cocinero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_pedido(self, client, camarero_user, cocinero_user, pedido):
        """Probar la actualización de un pedido con diferentes roles."""
        # Camarero puede actualizar observaciones
        update_data = {
            "observaciones": "Observaciones actualizadas"
        }
        response = client.put(
            f"/pedidos/{pedido['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["observaciones"] == "Observaciones actualizadas"
        
        # Camarero puede marcar como entregado
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
        
        # Cocinero puede marcar como en preparación
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
        
        # Cocinero puede marcar como listo
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

    def test_update_pedido_cocinero_limitado(self, client, cocinero_user, pedido):
        """Probar que los cocineros tienen permisos limitados para actualizar pedidos."""
        # Cocinero no debería poder cambiar observaciones
        update_data = {
            "observaciones": "Intento no autorizado"
        }
        response = client.put(
            f"/pedidos/{pedido['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {cocinero_user['token']}"}
        )
        # Verificar que la actualización no realiza cambios en las observaciones
        # o que falla explícitamente
        if response.status_code == status.HTTP_200_OK:
            assert response.json()["observaciones"] != "Intento no autorizado"

    def test_add_detalle_pedido(self, client, camarero_user, pedido, producto):
        """Probar la adición de un detalle a un pedido existente."""
        detalle_data = {
            "producto_id": producto["id"],
            "cantidad": 3,
            "observaciones": "Detalle adicional"
        }
        response = client.post(
            f"/pedidos/{pedido['id']}/detalles/",
            json=detalle_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["producto_id"] == producto["id"]
        assert response.json()["cantidad"] == 3
        assert response.json()["observaciones"] == "Detalle adicional"
        
        # Verificar que el detalle se ha añadido al pedido
        get_response = client.get(
            f"/pedidos/{pedido['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert len(get_response.json()["detalles"]) >= 2

    def test_update_detalle_pedido(self, client, camarero_user, cocinero_user, pedido):
        """Probar la actualización de un detalle de pedido."""
        # Obtener el ID del primer detalle
        get_response = client.get(
            f"/pedidos/{pedido['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        detalle_id = get_response.json()["detalles"][0]["id"]
        
        # Camarero puede actualizar un detalle
        update_data = {
            "cantidad": 5,
            "observaciones": "Observaciones actualizadas del detalle"
        }
        response = client.put(
            f"/pedidos/{pedido['id']}/detalles/{detalle_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["cantidad"] == 5
        assert response.json()["observaciones"] == "Observaciones actualizadas del detalle"
        
        # Cocinero sin especificar estado recibe error de validación
        update_data = {
            "cantidad": 2
        }
        response = client.put(
            f"/pedidos/{pedido['id']}/detalles/{detalle_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {cocinero_user['token']}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Cocinero intentando usar un estado no permitido
        update_data = {
            "estado": EstadoPedido.CANCELADO
        }
        response = client.put(
            f"/pedidos/{pedido['id']}/detalles/{detalle_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {cocinero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_detalle_pedido(self, client, camarero_user, pedido, producto):
        """Probar la eliminación de un detalle de pedido."""
        # Añadir un nuevo detalle para eliminar
        detalle_data = {
            "producto_id": producto["id"],
            "cantidad": 1
        }
        add_response = client.post(
            f"/pedidos/{pedido['id']}/detalles/",
            json=detalle_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        detalle_id = add_response.json()["id"]
        
        # Eliminar el detalle
        response = client.delete(
            f"/pedidos/{pedido['id']}/detalles/{detalle_id}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que el detalle ha sido eliminado
        get_response = client.get(
            f"/pedidos/{pedido['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        detalles_ids = [d["id"] for d in get_response.json()["detalles"]]
        assert detalle_id not in detalles_ids 