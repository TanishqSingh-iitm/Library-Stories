import requests
import time

BASE_URL = 'http://localhost:5000'  # Replace with your actual Flask app URL

def create_book(section_id, title, author):
    endpoint = f'/api/sections/{section_id}/books'
    data = {'title': title, 'author': author, 'price':10}
    response = requests.post(BASE_URL + endpoint, json=data)
    if response.status_code == 201:
        print(f"Book created successfully! Book ID: {response.json()['id']}")
    else:
        print(f"Error creating book. Status code: {response.status_code}")


def update_book(section_id, book_id, title, author):
    endpoint = f'/api/sections/{section_id}/books/{book_id}'
    data = {'title': title, 'author': author, 'price':100}
    response = requests.put(BASE_URL + endpoint, json=data)
    if response.status_code == 200:
        print(f"Book {book_id} updated successfully")
    else:
        print(f"Error updating book {book_id}. Status code: {response.status_code}")

def delete_book(section_id, book_id):
    endpoint = f'/api/sections/{section_id}/books/{book_id}'
    response = requests.delete(BASE_URL + endpoint)
    if response.status_code == 200:
        print(f"Book {book_id} deleted successfully")
    else:
        print(f"Error deleting book {book_id}. Status code: {response.status_code}")

if __name__ == '__main__':
    section_id = 9  # Replace with the actual section ID
    create_book(section_id, 'Book A', 'Author A')
    create_book(section_id, 'Book B', 'Author B')
    time.sleep(20)
    update_book(section_id, 29, 'Updated Book A', 'Updated Author A')
    print("Update Done")
    time.sleep(20)
    delete_book(section_id, 30)
    print("Delete Done")
