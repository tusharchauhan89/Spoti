import requests

url = 'http://127.0.0.1:5000/login'
data = {
    "email": "test@example.com",
    "password": "test123"
}

res = requests.post(url, json=data)
print(res.status_code)
print(res.json())
