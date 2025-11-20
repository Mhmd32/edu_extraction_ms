"""
Test script for the Question Extraction API

This script demonstrates how to use the extraction and question management endpoints.

Usage:
    python test_extraction_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_create_user():
    """Test creating a new user."""
    print("\n=== Testing User Creation ===")
    
    url = f"{BASE_URL}/users"
    data = {
        "username": "teacher1",
        "password": "test123",
        "display_name": "أستاذ أحمد",
        "is_admin": False,
        "is_active": True
    }
    
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_login(username, password):
    """Test user login."""
    print("\n=== Testing Login ===")
    
    url = f"{BASE_URL}/login"
    data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_list_users():
    """Test listing users."""
    print("\n=== Testing List Users ===")
    
    url = f"{BASE_URL}/users"
    response = requests.get(url, params={"limit": 10})
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_extract_questions(pdf_path):
    """Test question extraction from PDF."""
    print("\n=== Testing Question Extraction ===")
    
    url = f"{BASE_URL}/extract"
    
    # Prepare the file and data
    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path, f, "application/pdf")}
        data = {
            "subject_name": "الرياضيات",
            "class_name": "الصف الثاني عشر",
            "specialization": "علمي",
            "uploaded_by": "teacher1"
        }
        
        response = requests.post(url, files=files, data=data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_list_questions():
    """Test listing questions."""
    print("\n=== Testing List Questions ===")
    
    url = f"{BASE_URL}/questions"
    params = {
        "subject_name": "الرياضيات",
        "limit": 5
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    questions = response.json()
    print(f"Found {len(questions)} questions")
    
    if questions:
        print("\nFirst question:")
        print(json.dumps(questions[0], indent=2, ensure_ascii=False))


def test_list_questions_with_filters():
    """Test listing questions with various filters."""
    print("\n=== Testing List Questions with Filters ===")
    
    url = f"{BASE_URL}/questions"
    
    # Test different filters
    filters = [
        {"subject_name": "الرياضيات"},
        {"question_type": "Descriptive"},
        {"question_difficulty": "Medium"},
        {"class_name": "الصف الثاني عشر"}
    ]
    
    for filter_params in filters:
        response = requests.get(url, params=filter_params)
        count = len(response.json())
        print(f"Filter {filter_params}: Found {count} questions")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Question Extraction API Test Suite")
    print("=" * 60)
    
    try:
        # Test user management
        test_create_user()
        test_login("teacher1", "test123")
        test_list_users()
        
        # Test question extraction (uncomment and provide a PDF path)
        # test_extract_questions("path/to/your/textbook.pdf")
        
        # Test question listing
        test_list_questions()
        test_list_questions_with_filters()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API server.")
        print("Make sure the server is running at http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()

