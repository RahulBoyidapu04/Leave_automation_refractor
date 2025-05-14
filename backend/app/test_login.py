import httpx

def test_login_and_profile():
    base_url = "http://localhost:8000"
    
    # Login request
    data = {
        "username": "rahulboy",
        "password": "rahulboy123"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = httpx.post(f"{base_url}/auth/token", data=data, headers=headers)

    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]

    # Authenticated profile request
    profile_response = httpx.get(f"{base_url}/me", headers={"Authorization": f"Bearer {token}"})
    assert profile_response.status_code == 200, f"Profile fetch failed: {profile_response.text}"
    print("✅ Login + /me test passed")

if __name__ == "__main__":
    test_login_and_profile()