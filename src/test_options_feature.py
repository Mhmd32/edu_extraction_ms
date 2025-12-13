"""
Test script for Multiple Choice Options feature

This script demonstrates and tests the new option fields functionality.

Usage:
    python test_options_feature.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_get_multiple_choice_questions():
    """Test getting multiple choice questions with options."""
    print("\n=== Testing Multiple Choice Questions ===")
    
    url = f"{BASE_URL}/questions"
    params = {
        "question_type": "Multiple Choice",
        "limit": 10
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        questions = response.json()
        print(f"Found {len(questions)} multiple choice question(s)")
        
        if questions:
            print("\n--- Sample Multiple Choice Question ---")
            q = questions[0]
            print(f"Question ID: {q['id']}")
            print(f"Subject: {q['subject_name']}")
            print(f"Lesson: {q['lesson_title']}")
            print(f"Type: {q['question_type']}")
            print(f"Difficulty: {q['question_difficulty']}")
            print(f"\nQuestion Text:")
            print(f"  {q['question']}")
            
            print(f"\nOptions:")
            option_count = 0
            for i in range(1, 7):
                option_key = f"option{i}"
                if q.get(option_key):
                    print(f"  {i}. {q[option_key]}")
                    option_count += 1
            
            if option_count == 0:
                print("  ⚠️  No options found (might need to re-extract PDF)")
            else:
                print(f"\n✅ Found {option_count} option(s)")
            
            if q.get('correct_answer'):
                print(f"\nCorrect Answer: {q['correct_answer']}")
            
            if q.get('answer_steps'):
                print(f"\nAnswer Steps: {q['answer_steps']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def test_get_questions_with_options():
    """Test getting all questions and filter those with options."""
    print("\n=== Testing Questions with Options ===")
    
    url = f"{BASE_URL}/questions"
    params = {"limit": 100}
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        questions = response.json()
        print(f"Total questions retrieved: {len(questions)}")
        
        # Filter questions that have at least one option
        questions_with_options = [
            q for q in questions 
            if any(q.get(f"option{i}") for i in range(1, 7))
        ]
        
        print(f"Questions with options: {len(questions_with_options)}")
        
        # Count options per question
        if questions_with_options:
            print("\n--- Option Counts ---")
            for q in questions_with_options[:5]:  # Show first 5
                option_count = sum(1 for i in range(1, 7) if q.get(f"option{i}"))
                print(f"  '{q['question'][:50]}...' - {option_count} option(s)")
        else:
            print("\n⚠️  No questions with options found.")
            print("This is expected if you haven't extracted any PDFs yet,")
            print("or if you're using a database from before the options feature was added.")
    else:
        print(f"❌ Error: {response.status_code}")


def test_display_quiz_format():
    """Display multiple choice questions in quiz format."""
    print("\n=== Quiz Format Display ===")
    
    url = f"{BASE_URL}/questions"
    params = {
        "question_type": "Multiple Choice",
        "limit": 3
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        questions = response.json()
        
        if not questions:
            print("No multiple choice questions found.")
            return
        
        print(f"Found {len(questions)} question(s). Displaying quiz format:\n")
        print("=" * 70)
        
        for idx, q in enumerate(questions, 1):
            print(f"\nQuestion {idx}:")
            print(f"{q['question']}")
            print(f"\nDifficulty: {q.get('question_difficulty', 'N/A')}")
            print(f"\nChoose one:")
            
            has_options = False
            for i in range(1, 7):
                option_key = f"option{i}"
                if q.get(option_key):
                    print(f"  {q[option_key]}")
                    has_options = True
            
            if not has_options:
                print("  (No options available)")
            
            if q.get('correct_answer'):
                print(f"\nCorrect Answer: {q['correct_answer']}")
            
            print("-" * 70)
    else:
        print(f"❌ Error: {response.status_code}")


def test_filter_by_subject_and_type():
    """Test filtering questions by subject and type."""
    print("\n=== Testing Filter by Subject and Type ===")
    
    subjects = ["الرياضيات", "الفيزياء", "الكيمياء", "الأحياء"]
    
    for subject in subjects:
        url = f"{BASE_URL}/questions"
        params = {
            "subject_name": subject,
            "question_type": "Multiple Choice",
            "limit": 100
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            questions = response.json()
            questions_with_options = [
                q for q in questions 
                if any(q.get(f"option{i}") for i in range(1, 7))
            ]
            
            print(f"  {subject}: {len(questions)} total, {len(questions_with_options)} with options")
        else:
            print(f"  {subject}: Error {response.status_code}")


def test_option_field_structure():
    """Test the structure of option fields in the API response."""
    print("\n=== Testing Option Field Structure ===")
    
    url = f"{BASE_URL}/questions"
    params = {"limit": 1}
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        questions = response.json()
        
        if questions:
            q = questions[0]
            print("Checking if all option fields are present in API response:")
            
            expected_fields = ['option1', 'option2', 'option3', 'option4', 'option5', 'option6']
            
            for field in expected_fields:
                if field in q:
                    value = q[field]
                    if value:
                        print(f"  ✅ {field}: '{value[:50]}...' (populated)")
                    else:
                        print(f"  ✅ {field}: null (empty)")
                else:
                    print(f"  ❌ {field}: MISSING FROM RESPONSE")
            
            print("\n✅ All option fields are present in the API response structure")
        else:
            print("No questions in database to test")
    else:
        print(f"❌ Error: {response.status_code}")


def test_comprehension_questions():
    """Test getting comprehension questions with passages."""
    print("\n=== Testing Comprehension Questions ===")
    
    url = f"{BASE_URL}/questions"
    params = {
        "question_type": "Comprehension",
        "limit": 5
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        questions = response.json()
        print(f"Found {len(questions)} comprehension question(s)")
        
        if questions:
            print("\n--- Sample Comprehension Question ---")
            q = questions[0]
            print(f"Question ID: {q['id']}")
            print(f"Subject: {q['subject_name']}")
            print(f"Type: {q['question_type']}")
            
            print(f"\n📖 Passage (in option1):")
            passage = q.get('option1')
            if passage:
                # Show first 200 characters of passage
                print(f"  {passage[:200]}{'...' if len(passage) > 200 else ''}")
                print(f"  (Total passage length: {len(passage)} characters)")
            else:
                print("  ⚠️  No passage found in option1")
            
            print(f"\n❓ Question:")
            print(f"  {q['question']}")
            
            if q.get('correct_answer'):
                print(f"\n✅ Answer:")
                print(f"  {q['correct_answer']}")
        else:
            print("\n⚠️  No comprehension questions found.")
            print("Extract PDFs with reading comprehension questions to test this feature.")
    else:
        print(f"❌ Error: {response.status_code}")


def test_display_comprehension_format():
    """Display comprehension questions in a readable format."""
    print("\n=== Comprehension Question Display Format ===")
    
    url = f"{BASE_URL}/questions"
    params = {
        "question_type": "Comprehension",
        "limit": 2
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        questions = response.json()
        
        if not questions:
            print("No comprehension questions found.")
            return
        
        print(f"Found {len(questions)} question(s). Displaying:\n")
        print("=" * 70)
        
        for idx, q in enumerate(questions, 1):
            print(f"\n📚 Question {idx}:")
            print("-" * 70)
            
            # Display passage
            if q.get('option1'):
                print("\n📖 Read the following passage:\n")
                print(f"{q['option1']}\n")
                print("-" * 70)
            
            # Display question
            print(f"\n❓ {q['question']}")
            
            # Display answer if available
            if q.get('correct_answer'):
                print(f"\n✅ Answer: {q['correct_answer']}")
            
            print("\n" + "=" * 70)
    else:
        print(f"❌ Error: {response.status_code}")


def main():
    """Run all tests."""
    print("=" * 70)
    print("Question Features Test Suite")
    print("=" * 70)
    
    try:
        # Test option field structure
        test_option_field_structure()
        
        # Test getting multiple choice questions
        test_get_multiple_choice_questions()
        
        # Test questions with options
        test_get_questions_with_options()
        
        # Test filtering
        test_filter_by_subject_and_type()
        
        # Display quiz format
        test_display_quiz_format()
        
        # Test comprehension questions
        test_comprehension_questions()
        
        # Display comprehension format
        test_display_comprehension_format()
        
        print("\n" + "=" * 70)
        print("All tests completed!")
        print("=" * 70)
        
        print("\n📝 Notes:")
        print("  - If no options are found, you may need to:")
        print("    1. Run the database migration (migrate_add_options.py)")
        print("    2. Extract new PDFs with multiple choice questions")
        print("    3. Re-extract existing PDFs to get options")
        print("\n  - For comprehension questions:")
        print("    1. Extract PDFs with reading comprehension passages")
        print("    2. Questions like 'Read the passage and answer...'")
        print("    3. The passage will be stored in option1 field")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API server.")
        print("Make sure the server is running at http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()

