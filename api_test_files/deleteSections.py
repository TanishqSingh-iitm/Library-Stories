import requests

BASE_URL = 'http://localhost:5000'

def delete_section(section_id):
    endpoint = f'/api/sections/{section_id}'
    response = requests.delete(BASE_URL + endpoint)
    if response.status_code == 200:
        print(f"Section {section_id} deleted successfully")
    else:
        print(f"Error deleting section {section_id}. Status code: {response.status_code}")

if __name__ == '__main__':
    section_id_to_delete = 10
    delete_section(section_id_to_delete)
