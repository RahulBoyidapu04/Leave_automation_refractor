# tests/test_apply_leave.py

def test_apply_leave_invalid_date(client):
    payload = {
        "leave_type": "Annual",
        "start_date": "2025-XX-10",
        "end_date": "2025-12-20",
        "backup_person": "John"
    }

    response = client.post("/apply-leave", json=payload)
    assert response.status_code in (400, 422)

def test_profile_requires_auth(client):
    res = client.get("/me")
    assert res.status_code == 401  # since JWT is not mocked yet
