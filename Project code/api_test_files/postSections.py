import requests

# Replace with your actual Flask app URL
BASE_URL = 'http://localhost:5000'

def create_section():
    endpoint = '/api/sections'
    data = {
        'name': 'API Section',
        'desc': 'Books related to API Section'
    }

    response = requests.post(BASE_URL + endpoint, json=data)
    if response.status_code == 201:
        print(f"Section created successfully! Section ID: {response.json()['id']}")
    else:
        print(f"Error creating section. Status code: {response.status_code}")

if __name__ == '__main__':
    create_section()
