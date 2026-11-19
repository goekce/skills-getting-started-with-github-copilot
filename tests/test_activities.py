import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Play chess",
            "schedule": "Fridays",
            "max_participants": 3,
            "participants": ["existing@example.com"],
        },
        "Art Club": {
            "description": "Make art",
            "schedule": "Mondays",
            "max_participants": 5,
            "participants": [],
        },
    }
    monkeypatch.setattr(app_module, "activities", activities)
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_details_and_participants(client):
    # Arrange
    expected = {
        "description": "Play chess",
        "schedule": "Fridays",
        "max_participants": 3,
        "participants": ["existing@example.com"],
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"] == expected
    assert response.json()["Art Club"]["participants"] == []


def test_signup_appears_in_subsequent_activities_response(client):
    # Arrange
    email = "new+student@example.com"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    activities = client.get("/activities").json()

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    assert activities["Chess Club"]["participants"] == ["existing@example.com", email]
    assert activities["Art Club"]["participants"] == []


def test_duplicate_signup_does_not_change_participants(client):
    # Arrange
    email = "existing@example.com"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    participants = client.get("/activities").json()["Chess Club"]["participants"]

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert participants == [email]


def test_unregister_disappears_from_subsequent_activities_response(client):
    # Arrange
    email = "existing@example.com"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})
    activities = client.get("/activities").json()

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from Chess Club"
    assert activities["Chess Club"]["participants"] == []
    assert activities["Art Club"]["participants"] == []


def test_unregister_missing_participant_does_not_change_participants(client):
    # Arrange
    email = "missing@example.com"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})
    participants = client.get("/activities").json()["Chess Club"]["participants"]

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert participants == ["existing@example.com"]


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_unknown_activity_returns_not_found(client, method):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.request(method, "/activities/Unknown/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_signup_endpoint_requires_email(client, method):
    # Arrange
    url = "/activities/Chess Club/signup"

    # Act
    response = client.request(method, url)

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]
