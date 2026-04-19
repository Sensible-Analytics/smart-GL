import requests

# Sandbox Environment
base_url = "https://sandbox.basiq.io"

# Sandbox API key (starts with test_)
api_key = "test_your_api_key_here"

# Test Bank
institution_id = "AU00000"

# Test User
username = "ashMann"
password = "hooli2024"

# Step 1: Get access token
auth_url = f"{base_url}/token"
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = {"grant_type": "client_credentials", "client_id": api_key}
response = requests.post(auth_url, headers=headers, data=data)
access_token = response.json()["access_token"]

# Step 2: Create test user
users_url = f"{base_url}/users"
headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
data = {
    "username": username,
    "password": password,
    "email": f"{username}@example.com"
}
response = requests.post(users_url, headers=headers, json=data)
user_id = response.json()["id"]

# Step 3: Create connection with institution and credentials
connections_url = f"{base_url}/users/{user_id}/connections"
headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
data = {
    "institution": {"id": institution_id},
    "credentials": {"id": username, "password": password}
}
response = requests.post(connections_url, headers=headers, json=data)
job_id = response.json()["id"]

# Step 4: Wait for job to complete
jobs_url = f"{base_url}/jobs/{job_id}"
while True:
    response = requests.get(jobs_url, headers={"Authorization": f"Bearer {access_token}"})
    job_status = response.json()["status"]
    if job_status == "completed":
        break
    else:
        import time
        time.sleep(1)

# Step 5: Get active connection
connections_url = f"{base_url}/users/{user_id}/connections"
response = requests.get(connections_url, headers={"Authorization": f"Bearer {access_token}"})
active_connection = None
for connection in response.json()["data"]:
    if connection["status"] == "active":
        active_connection = connection["id"]
        break

# Step 6: Get accounts
accounts_url = f"{base_url}/users/{user_id}/accounts"
response = requests.get(accounts_url, headers={"Authorization": f"Bearer {access_token}"})
accounts = response.json()["data"]

print(accounts)