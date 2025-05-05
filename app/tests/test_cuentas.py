"""
Tests para los endpoints de gestión de cuentas.
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta

@pytest.fixture
def mesa(client, admin_user):
    """Crear una mesa de prueba y devolver sus datos."""
    mesa_data = {
        "numero": 99,
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
        "nombre": "Test Categoria Cuenta",
        "descripcion": "Categoria para pruebas de cuentas"
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
        "nombre": "Test Producto Cuenta",
        "descripcion": "Producto para pruebas de cuentas",
        "precio": 9.99,
        "tiempo_preparacion": 15,
        "categoria_id": categoria["id"],
        "tipo": "comida",
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
        "observaciones": "Pedido para test de cuenta",
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

@pytest.fixture
def cuenta(client, camarero_user, mesa, pedido):
    """Crear una cuenta de prueba y devolver sus datos."""
    # Primero cambiamos el estado de la mesa a ocupada
    response = client.put(
        f"/mesas/{mesa['id']}",
        json={"estado": "ocupada"},
        headers={"Authorization": f"Bearer {camarero_user['token']}"}
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Ahora cerramos la mesa para generar la cuenta
    response = client.put(
        f"/mesas/{mesa['id']}",
        json={"estado": "libre"},
        headers={"Authorization": f"Bearer {camarero_user['token']}"}
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Obtenemos la cuenta generada
    response = client.get(
        "/cuentas/",
        headers={"Authorization": f"Bearer {camarero_user['token']}"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) > 0
    
    return response.json()[0]

class TestCuentas:
    def test_get_cuentas(self, client, admin_user, camarero_user, cuenta):
        """Probar la obtención de todas las cuentas."""
        # Admin puede ver todas las cuentas
        response = client.get(
            "/cuentas/",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Camarero solo puede ver sus propias cuentas
        response = client.get(
            "/cuentas/",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        # Verificar que todas las cuentas son de este camarero
        for c in response.json():
            assert c["camarero_id"] == camarero_user["id"]
    
    def test_get_cuenta_by_id(self, client, admin_user, camarero_user, cuenta):
        """Probar la obtención de una cuenta específica por ID."""
        # Admin puede ver cualquier cuenta
        response = client.get(
            f"/cuentas/{cuenta['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == cuenta["id"]
        
        # Camarero puede ver su propia cuenta
        response = client.get(
            f"/cuentas/{cuenta['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == cuenta["id"]
    
    def test_create_cuenta_manual(self, client, camarero_user, admin_user):
        """Probar la creación manual de una cuenta."""
        cuenta_data = {
            "numero_mesa": 101,
            "nombre_camarero": "Test Camarero",
            "total": 25.99,
            "metodo_pago": "efectivo",
            "detalles": [
                {
                    "pedido_id": 1,
                    "producto_id": 1,
                    "nombre_producto": "Producto Test",
                    "cantidad": 2,
                    "precio_unitario": 12.99,
                    "subtotal": 25.98,
                    "observaciones": "Observaciones test"
                }
            ]
        }
        response = client.post(
            "/cuentas/",
            json=cuenta_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["total"] == 25.99
        assert response.json()["nombre_camarero"] == "Test Camarero"
        
        # Verificar si un cocinero puede crear cuentas (no debería)
        # TODO: Agregar test para verificar que un cocinero no puede crear cuentas
    
    def test_update_cuenta(self, client, admin_user, camarero_user, cuenta):
        """Probar la actualización de una cuenta."""
        update_data = {
            "metodo_pago": "tarjeta"
        }
        response = client.put(
            f"/cuentas/{cuenta['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["metodo_pago"] == "tarjeta"
    
    def test_generar_cuenta_mesa(self, client, camarero_user, mesa, pedido):
        """Probar la generación de datos para una cuenta desde los pedidos de una mesa."""
        # Poner la mesa en estado ocupada
        response = client.put(
            f"/mesas/{mesa['id']}",
            json={"estado": "ocupada"},
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Generar datos para la cuenta
        response = client.get(
            f"/cuentas/generar/mesa/{mesa['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["mesa_id"] == mesa["id"]
        assert data["numero_mesa"] == mesa["numero"]
        assert "detalles" in data
        assert len(data["detalles"]) > 0
        assert data["total"] > 0
    
    def test_get_resumen_cuentas(self, client, admin_user, camarero_user, cuenta):
        """Probar la obtención del resumen de cuentas (solo para administradores)."""
        # Admin puede ver el resumen
        response = client.get(
            "/cuentas/resumen",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "total_ingresos" in response.json()
        assert "total_cuentas" in response.json()
        
        # Camarero no puede ver el resumen
        response = client.get(
            "/cuentas/resumen",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN 