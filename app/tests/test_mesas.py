"""
Tests for table management endpoints.
"""
import pytest
from fastapi import status
from app.core.enums import EstadoMesa

@pytest.fixture
def mesa(client, admin_user):
    """Create a test table and return its data."""
    mesa_data = {
        "numero": 1,
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

class TestMesas:
    def test_create_mesa(self, client, admin_user):
        """Test creating a new table."""
        mesa_data = {
            "numero": 2,
            "capacidad": 6,
            "ubicacion": "Terraza"
        }
        response = client.post(
            "/mesas/",
            json=mesa_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["numero"] == 2
        assert response.json()["capacidad"] == 6
        assert response.json()["ubicacion"] == "Terraza"
        assert response.json()["estado"] == EstadoMesa.LIBRE  # Default state
        assert "id" in response.json()

    def test_create_mesa_duplicate(self, client, admin_user, mesa):
        """Test creating a table with a duplicate number."""
        mesa_data = {
            "numero": mesa["numero"],  # Same number as existing table
            "capacidad": 8,
            "ubicacion": "Exterior"
        }
        response = client.post(
            "/mesas/",
            json=mesa_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_mesa_unauthorized(self, client, camarero_user):
        """Test that non-admin users cannot create tables."""
        mesa_data = {
            "numero": 3,
            "capacidad": 2,
            "ubicacion": "Barra"
        }
        response = client.post(
            "/mesas/",
            json=mesa_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_mesas(self, client, admin_user, camarero_user, mesa):
        """Test getting all tables."""
        # Admin request
        response = client.get(
            "/mesas/",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1
        
        # Camarero request
        response = client.get(
            "/mesas/",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Test with filter - Use the string value directly for the query parameter
        response = client.get(
            "/mesas/?estado=libre",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert all(m["estado"] == EstadoMesa.LIBRE for m in response.json())

    def test_get_mesa_by_id(self, client, admin_user, mesa):
        """Test getting a specific table by ID."""
        response = client.get(
            f"/mesas/{mesa['id']}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == mesa["id"]
        assert response.json()["numero"] == mesa["numero"]
        assert response.json()["estado"] == mesa["estado"]

    def test_update_mesa(self, client, admin_user, mesa):
        """Test updating a table."""
        update_data = {
            "capacidad": 10,
            "estado": EstadoMesa.MANTENIMIENTO,
            "ubicacion": "VIP"
        }
        response = client.put(
            f"/mesas/{mesa['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["capacidad"] == 10
        assert response.json()["estado"] == EstadoMesa.MANTENIMIENTO
        assert response.json()["ubicacion"] == "VIP"

    def test_update_mesa_unauthorized(self, client, camarero_user, mesa):
        """Test that non-admin users cannot update tables."""
        update_data = {
            "estado": EstadoMesa.OCUPADA
        }
        response = client.put(
            f"/mesas/{mesa['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_mesa(self, client, admin_user):
        """Test deleting a table."""
        # Create a table to delete
        mesa_data = {
            "numero": 99,
            "capacidad": 2,
            "ubicacion": "Para borrar"
        }
        create_response = client.post(
            "/mesas/",
            json=mesa_data,
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        mesa_id = create_response.json()["id"]
        
        # Delete the table
        response = client.delete(
            f"/mesas/{mesa_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify the table is deleted
        get_response = client.get(
            f"/mesas/{mesa_id}",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_mesa_unauthorized(self, client, camarero_user, mesa):
        """Test that non-admin users cannot delete tables."""
        response = client.delete(
            f"/mesas/{mesa['id']}",
            headers={"Authorization": f"Bearer {camarero_user['token']}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN 