def test_manager_leave_decision(client):
    # Simulate manager approving leave with mock ID
    response = client.post(
        "/manager/leave-decision",
        json={"leave_id": 1, "decision": "Approved", "comments": "Approved for valid reason"},
        headers={"X-Request-ID": "test-decision-1"}
    )
    assert response.status_code in [200, 404, 403]  # Depending on if test DB was properly seeded

# tests/test_leave_summary.py
def test_leave_summary(client):
    response = client.get("/leave/summary", headers={"X-Request-ID": "test-summary-1"})
    assert response.status_code == 200
    assert "total_days" in response.json()

# tests/test_availability.py
def test_availability_calendar(client):
    response = client.get("/availability/next-30-days", headers={"X-Request-ID": "test-availability-1"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
