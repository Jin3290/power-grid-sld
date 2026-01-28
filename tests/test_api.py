import pytest
import random
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# Test authentication
def test_login():
    response = client.post("/login", params={"username": "manager", "password": "manager123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def get_headers():
    token = test_login()
    return {"Authorization": f"Bearer {token}"}


# Test component creation and validation with large dataset
def test_create_100_components():
    """Test creating 100 components"""
    headers = get_headers()

    components = []
    for i in range(100):
        if i < 40:  # 40 transformers
            component_data = {
                "name": f"Transformer_{i}",
                "substation": f"Sub_{i % 10}",
                "component_type": "transformer",
                "capacity_mva": random.uniform(10, 500),
                "voltage_kv": random.choice([110, 220, 400])
            }
        elif i < 80:  # 40 lines
            component_data = {
                "name": f"Line_{i}",
                "substation": f"Sub_{i % 10}",
                "component_type": "line",
                "length_km": random.uniform(1, 100),
                "voltage_kv": random.choice([110, 220, 400])
            }
        else:  # 20 switches
            component_data = {
                "name": f"Switch_{i}",
                "substation": f"Sub_{i % 10}",
                "component_type": "switch",
                "status": random.choice(["open", "closed"])
            }

        response = client.post("/components", json=component_data, headers=headers)
        assert response.status_code == 200
        components.append(response.json())

    return components


def test_create_measurements():
    """Test creating 10,000 measurements per component type"""
    headers = get_headers()

    # First create components
    components = test_create_100_components()

    # Create measurements for each component
    for component in components:
        for _ in range(100):  # 100 measurements per component = 10,000 total
            measurement_data = {
                "value": random.uniform(100, 1000),
                "measurement_type": random.choice(["Voltage", "Current", "Power"]),
                "component_id": component["id"],
                "timestamp": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
            }

            response = client.post("/measurements", json=measurement_data, headers=headers)
            assert response.status_code == 200


def test_generate_report():
    """Test report generation"""
    headers = get_headers()

    # Generate components and measurements first
    test_create_measurements()

    # Create report
    start_date = (datetime.now() - timedelta(days=30)).isoformat()
    end_date = datetime.now().isoformat()

    response = client.post(
        "/reports",
        params={"start_date": start_date, "end_date": end_date},
        headers=headers
    )
    assert response.status_code == 200
    report_id = response.json()["report_id"]

    # Wait and check report
    import time
    time.sleep(3)  # Wait for async processing

    response = client.get(f"/reports/{report_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


if __name__ == "__main__":
    pytest.main([__file__])
