"""
IntelliMaint AI — FastAPI REST API Endpoints & Integration Tests
"""

import pytest
from fastapi import status


def test_health_endpoint(client):
    """Test 1: Health check endpoint responds with 200 OK and database + ML readiness."""
    resp = client.get("/health")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert "machine_learning" in data


def test_machine_endpoints_crud(client):
    """Test 3: Verify Machine CRUD endpoints via HTTP requests."""
    # 1. Create machine
    payload = {
        "machine_id": "CNC-ROUTER-01",
        "name": "3-Axis Wood & Composite Router",
        "machine_type": "CNC Milling Machine",
        "department": "Carpentry Bay",
        "operational_status": "OPERATIONAL",
    }
    post_resp = client.post("/api/v1/machines", json=payload)
    assert post_resp.status_code == status.HTTP_201_CREATED
    assert post_resp.json()["machine_id"] == "CNC-ROUTER-01"

    # 2. Duplicate machine registration returns 409 Conflict
    dup_resp = client.post("/api/v1/machines", json=payload)
    assert dup_resp.status_code == status.HTTP_409_CONFLICT

    # 3. Get machine by ID
    get_resp = client.get("/api/v1/machines/CNC-ROUTER-01")
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["name"] == "3-Axis Wood & Composite Router"

    # 4. Patch machine
    patch_resp = client.patch(
        "/api/v1/machines/CNC-ROUTER-01",
        json={"operational_status": "DEGRADED", "notes": "Bearing noise observed"},
    )
    assert patch_resp.status_code == status.HTTP_200_OK
    assert patch_resp.json()["operational_status"] == "DEGRADED"

    # 5. Delete machine
    del_resp = client.delete("/api/v1/machines/CNC-ROUTER-01")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # 6. Verify 404 after deletion
    get_del_resp = client.get("/api/v1/machines/CNC-ROUTER-01")
    assert get_del_resp.status_code == status.HTTP_404_NOT_FOUND


def test_invalid_request_body_returns_422(client):
    """Test 5: Submitting malformed or invalid request body triggers Pydantic HTTP 422 Unprocessable Entity."""
    # Missing required field 'machine_id' and 'name'
    resp = client.post("/api/v1/machines", json={"notes": "Incomplete machine"})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_telemetry_post_and_get(client, sample_machine):
    """Verify recording and querying single telemetry readings."""
    payload = {
        "machine_id": sample_machine.machine_id,
        "air_temperature": 298.5,
        "process_temperature": 308.7,
        "rotational_speed": 1500.0,
        "torque": 40.0,
        "tool_wear": 25.0,
        "machine_type_variant": "M",
    }
    resp = client.post("/api/v1/telemetry", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["machine_id"] == sample_machine.machine_id
    assert data["temp_diff"] == pytest.approx(10.2, abs=0.1)

    # Query telemetry
    list_resp = client.get(f"/api/v1/telemetry?machine_id={sample_machine.machine_id}")
    assert list_resp.status_code == status.HTTP_200_OK
    assert len(list_resp.json()) >= 1


def test_prediction_endpoint(client, sample_machine):
    """Verify failure risk prediction API endpoint."""
    payload = {
        "machine_id": sample_machine.machine_id,
        "air_temperature": 299.0,
        "process_temperature": 309.5,
        "rotational_speed": 1450.0,
        "torque": 42.0,
        "tool_wear": 50.0,
        "machine_type_variant": "M",
    }
    resp = client.post("/api/v1/predictions", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert "failure_probability" in data
    assert data["risk_category"] in ["Low", "Medium", "High"]
    assert "prediction_id" in data


def test_maintenance_endpoints(client, sample_machine):
    """Verify maintenance work order API endpoints."""
    wo_payload = {
        "machine_id": sample_machine.machine_id,
        "title": "Calibrate Spindle Tachometer",
        "priority": "Medium",
        "status": "Open",
    }
    create_resp = client.post("/api/v1/maintenance", json=wo_payload)
    assert create_resp.status_code == status.HTTP_201_CREATED
    wo_no = create_resp.json()["work_order_no"]

    # Patch status
    patch_resp = client.patch(
        f"/api/v1/maintenance/{wo_no}",
        json={"status": "In Progress", "technician": "Sam Vance"},
    )
    assert patch_resp.status_code == status.HTTP_200_OK
    assert patch_resp.json()["status"] == "In Progress"


def test_analytics_summary_endpoint(client, sample_machine):
    """Verify fleet analytics summary endpoint."""
    resp = client.get("/api/v1/analytics/summary")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "total_registered_machines" in data
    assert "risk_distribution" in data
    assert data["total_registered_machines"] >= 1
