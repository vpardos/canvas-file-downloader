import requests

def get_courses_list(url, token):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# We will print the list in a human readable format
def print_courses_list(courses):
    for course in courses:
        print(f"Term ID: {course['enrollment_term_id']}, Course ID: {course['id']}, Name: {course['name']}")
