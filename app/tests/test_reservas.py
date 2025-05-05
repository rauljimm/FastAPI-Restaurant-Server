"""
Tests for reservation management endpoints.
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta, UTC
from app.core.enums import EstadoReserva

@pytest.fixture
def mesa(client, admin_user):
    """Create a test table and return its data."""
    mesa_data = {
        "numero": 20,
        "capacidad": 6,
        "ubicacion": "Terraza"
    }
    response = client.post(
        "/mesas/",
        json=mesa_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

@pytest.fixture
def reserva(client, admin_user, mesa):
    """Create a test reservation and return its data."""
    # Create reservation for tomorrow
    tomorrow = datetime.now(UTC) + timedelta(days=1)
    reserva_data = {
        "cliente_nombre": "Cliente",
        "cliente_apellido": "Test",
        "cliente_telefono": "123456789",
        "cliente_email": "cliente@test.com",
        "fecha": tomorrow.isoformat(),
        "duracion": 120,
        "num_personas": 4,
        "mesa_id": mesa["id"],
        "observaciones": "Reserva de prueba"
    }
    response = client.post(
        "/reservas/",
        json=reserva_data,
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

class TestReservas:
    def test_create_reserva(self, client, admin_user, mesa):
        """Test creating a new reservation."""
        # Create reservation for tomorrow at dinner time
        tomorrow = datetime.now(UTC) + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=20, minute=0, second=0, microsecond=0)
        
        reserva_data = {
            "cliente_nombre": "Nuevo",
            "cliente_apellido": "Cliente",
            "cliente_telefono": "987654321",
            "cliente_email": "nuevo@cliente.com",
            "fecha": tomorrow.isoformat(),
            "duracion": 90,
            "num_personas": 2,
            "mesa_id": mesa["id"],
            "observaciones": "Nueva reserva"
        }
        response = client.post(
            "/reservas/",
            json=reserva_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["cliente_nombre"] == "Nuevo"
        assert response.json()["cliente_apellido"] == "Cliente"
        assert response.json()["num_personas"] == 2
        assert response.json()["mesa_id"] == mesa["id"]
        assert response.json()["estado"] == EstadoReserva.PENDIENTE  # Default state
        assert "id" in response.json()

    def test_create_reserva_fecha_pasada(self, client, admin_user, mesa):
        """Test creating a reservation with a past date."""
        yesterday = datetime.now(UTC) - timedelta(days=1)
        reserva_data = {
            "cliente_nombre": "Cliente",
            "cliente_apellido": "Pasado",
            "cliente_telefono": "123123123",
            "fecha": yesterday.isoformat(),
            "num_personas": 4,
            "mesa_id": mesa["id"]
        }
        response = client.post(
            "/reservas/",
            json=reserva_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_reserva_mesa_inexistente(self, client, admin_user):
        """Test creating a reservation with a non-existent table."""
        tomorrow = datetime.now(UTC) + timedelta(days=1)
        reserva_data = {
            "cliente_nombre": "Cliente",
            "cliente_apellido": "Test",
            "cliente_telefono": "123456789",
            "fecha": tomorrow.isoformat(),
            "num_personas": 4,
            "mesa_id": 999999  # ID no existente
        }
        response = client.post(
            "/reservas/",
            json=reserva_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_reserva_capacidad_excedida(self, client, admin_user, mesa):
        """Test creating a reservation with more people than table capacity."""
        tomorrow = datetime.now(UTC) + timedelta(days=1)
        reserva_data = {
            "cliente_nombre": "Cliente",
            "cliente_apellido": "Grande",
            "cliente_telefono": "123456789",
            "fecha": tomorrow.isoformat(),
            "num_personas": mesa["capacidad"] + 2,  # Exceeds capacity
            "mesa_id": mesa["id"]
        }
        response = client.post(
            "/reservas/",
            json=reserva_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_reservas(self, client, admin_user, camarero_user, reserva):
        """Test getting all reservations."""
        # Admin request
        response = client.get(
            "/reservas/",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Camarero request
        response = client.get(
            "/reservas/",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Test with filters
        response = client.get(
            f"/reservas/?estado=pendiente&mesa_id={reserva['mesa_id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        assert all(r["estado"] == EstadoReserva.PENDIENTE for r in response.json())
        assert all(r["mesa_id"] == reserva["mesa_id"] for r in response.json())

    def test_get_reserva_by_id(self, client, admin_user, reserva):
        """Test getting a specific reservation by ID."""
        response = client.get(
            f"/reservas/{reserva['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == reserva["id"]
        assert response.json()["cliente_nombre"] == reserva["cliente_nombre"]
        assert "mesa" in response.json()  # Check that it returns the detailed reservation with table info

    def test_update_reserva(self, client, admin_user, reserva):
        """Test updating a reservation."""
        update_data = {
            "cliente_nombre": "Cliente Actualizado",
            "num_personas": 5,
            "estado": EstadoReserva.CONFIRMADA
        }
        response = client.put(
            f"/reservas/{reserva['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["cliente_nombre"] == "Cliente Actualizado"
        assert response.json()["num_personas"] == 5
        assert response.json()["estado"] == EstadoReserva.CONFIRMADA

    def test_update_reserva_fecha(self, client, admin_user, reserva):
        """Test updating a reservation's date."""
        new_date = datetime.now(UTC) + timedelta(days=2)
        update_data = {
            "fecha": new_date.isoformat()
        }
        response = client.put(
            f"/reservas/{reserva['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        # Extract only the date part since we can't compare full datetimes directly
        expected_date = new_date.strftime("%Y-%m-%d")
        actual_date = datetime.fromisoformat(response.json()["fecha"]).strftime("%Y-%m-%d")
        assert actual_date == expected_date

    def test_update_reserva_fecha_pasada(self, client, admin_user, reserva):
        """Test updating a reservation to a past date."""
        yesterday = datetime.now(UTC) - timedelta(days=1)
        update_data = {
            "fecha": yesterday.isoformat()
        }
        response = client.put(
            f"/reservas/{reserva['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_reserva(self, client, admin_user, mesa):
        """Test deleting a reservation."""
        # Create a reservation to delete
        tomorrow = datetime.now(UTC) + timedelta(days=1)
        reserva_data = {
            "cliente_nombre": "Para",
            "cliente_apellido": "Eliminar",
            "cliente_telefono": "123456789",
            "fecha": tomorrow.isoformat(),
            "num_personas": 4,
            "mesa_id": mesa["id"]
        }
        create_response = client.post(
            "/reservas/",
            json=reserva_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        reserva_id = create_response.json()["id"]
        
        # Delete the reservation
        response = client.delete(
            f"/reservas/{reserva_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify the reservation is deleted
        get_response = client.get(
            f"/reservas/{reserva_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_reserva_by_camarero(self, client, camarero_user, reserva):
        """Test that camareros can delete reservations (updated permission)."""
        response = client.delete(
            f"/reservas/{reserva['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify the reservation is deleted
        get_response = client.get(
            f"/reservas/{reserva['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND 