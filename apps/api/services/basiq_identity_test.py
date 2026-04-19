import requests

# Sandbox Environment: Use your sandbox API key (starts with test_)
api_key = "test_your_api_key"

# Test Flow: Automated via API
def get_token(api_key):
    headers = {"Authorization": f"Basic {api_key}"}
    response = requests.post("https://api.basiq.io/v3/token", headers=headers)
    return response.json()["access_token"]

def create_test_user(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post("https://api.basiq.io/v3/users", headers=headers)
    return response.json()

def create_connection(access_token, user):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.basiq.io/v3/users/{user['id']}/connections"
    institution = {"id": "AU00000"}
    credentials = {"id": "test-user", "password": "test-password"}
    response = requests.post(url, headers=headers, json={"institution": institution, "credentials": credentials})
    return response.json()

def verify_connection(access_token, connection_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"https://api.basiq.io/v3/users/{connection_id}/jobs", headers=headers)
    job_id = response.json()["jobs"][0]["id"]
    while True:
        response = requests.get(f"https://api.basiq.io/v3/jobs/{job_id}", headers=headers)
        if response.json()["status"] == "completeted":
            break
        else:
            print("Connection is still being verified...")
            time.sleep(1)

def get_identity(access_token, user_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"https://api.basiq.io/v3/users/{user_id}/identity", headers=headers)
    return response.json()

def main():
    access_token = get_token(api_key)
    user = create_test_user(access_token)
    connection = create_connection(access_token, user)
    verify_connection(access_token, connection["id"])
    user_id = user["id"]
    identity = get_identity(access_token, user_id)
    print(identity)

main()