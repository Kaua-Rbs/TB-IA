from fastapi.testclient import TestClient

from backend.main import app
from backend.storage import repository


client = TestClient(app)


def setup_function() -> None:
    repository.reset()


def test_seed_alert_validation_action_and_dashboard_flow() -> None:
    seed_response = client.post("/seed/synthetic")
    assert seed_response.status_code == 200
    assert seed_response.json()["questionnaires_created"] == 6

    alerts_response = client.get("/alerts")
    assert alerts_response.status_code == 200
    alerts = alerts_response.json()
    assert len(alerts) > 0
    assert alerts[0]["score"] >= alerts[-1]["score"]

    alert_id = alerts[0]["id"]
    validation_response = client.post(
        f"/alerts/{alert_id}/validation",
        json={
            "decision": "validated",
            "validated_by": "enfermeira_demo",
            "note": "Validacao humana sintetica.",
        },
    )
    assert validation_response.status_code == 200
    assert validation_response.json()["status"] == "validated"

    action_response = client.post(
        f"/alerts/{alert_id}/actions",
        json={
            "action_type": "home_visit_scheduled",
            "performed_by": "acs_demo",
            "note": "Acao sintetica registrada.",
        },
    )
    assert action_response.status_code == 200
    assert action_response.json()["status"] == "completed"
    assert len(action_response.json()["actions"]) == 1

    dashboard_response = client.get("/dashboard/territories")
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert len(dashboard) == 3
    assert sum(item["questionnaires"] for item in dashboard) == 6


def test_disclaimer_states_system_limits() -> None:
    response = client.get("/disclaimer")
    assert response.status_code == 200
    body = response.json()
    assert "Nao diagnostica" in body["message"]
    assert "dados reais" in body["forbidden_use"]

