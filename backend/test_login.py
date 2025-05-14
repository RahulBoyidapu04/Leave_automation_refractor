import requests

url = "http://127.0.0.1:8000/token"
data = {
    "username": "rahulboy",
    "password": "rahulboy123"
}

response = requests.post(url, data=data)
print("Status Code:", response.status_code)
print("Response:", response.json())
