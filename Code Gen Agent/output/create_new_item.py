import requests

# Define the URL of the Flask app
target_url = "http://localhost:5000/items"

# Define the data to be sent as JSON
new_item_data = {
    "name": "New Item",
    "description": "This is a new item."
}

# Make a POST request to create the new item
def post_new_item():
    response = requests.post(target_url, json=new_item_data)

    # Check if the request was successful
    if response.status_code == 201:
        print('Item created successfully:', response.json())
    else:
        print('Failed to create item:', response.status_code)