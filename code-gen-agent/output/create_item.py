import requests

# Define the URL of the POST endpoint for creating a new item
url = 'http://localhost:5000/items'

# Data to be sent in the JSON payload
data = {
    "name": "New Item",
    "description": "This is a new item"
}

# Send a POST request to create a new item
response = requests.post(url, json=data)

# Check if the request was successful
if response.status_code == 201:
    print("Item created successfully:", response.json())
else:
    print("Failed to create item. Status code:", response.status_code)