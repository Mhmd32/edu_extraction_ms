# Delete Questions API Documentation

This document describes the new API endpoints for deleting questions from the database.

## Overview

Two new endpoints have been added to allow deletion of questions:

1. **DELETE a single question** by ID
2. **DELETE multiple questions** by providing a list of IDs

---

## API Endpoints

### 1. Delete a Single Question

**Endpoint:** `DELETE /questions/{question_id}`

**Description:** Delete a specific question by its UUID.

**Parameters:**
- `question_id` (path parameter, required): The UUID of the question to delete

**Example Request:**

```bash
curl -X DELETE "http://localhost:8000/questions/123e4567-e89b-12d3-a456-426614174000"
```

**Python Example:**

```python
import requests

BASE_URL = "http://localhost:8000"
question_id = "123e4567-e89b-12d3-a456-426614174000"

response = requests.delete(f"{BASE_URL}/questions/{question_id}")
print(response.json())
```

**Success Response (200):**

```json
{
  "status": "success",
  "message": "Successfully deleted question",
  "deleted_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Error Response (404 - Not Found):**

```json
{
  "detail": "Question with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

---

### 2. Delete Multiple Questions

**Endpoint:** `DELETE /questions`

**Description:** Delete multiple questions by providing a list of question UUIDs.

**Request Body:**

```json
{
  "question_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-a456-426614174001",
    "323e4567-e89b-12d3-a456-426614174002"
  ]
}
```

**Example Request:**

```bash
curl -X DELETE "http://localhost:8000/questions" \
  -H "Content-Type: application/json" \
  -d '{
    "question_ids": [
      "123e4567-e89b-12d3-a456-426614174000",
      "223e4567-e89b-12d3-a456-426614174001"
    ]
  }'
```

**Python Example:**

```python
import requests

BASE_URL = "http://localhost:8000"

question_ids = [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-a456-426614174001",
    "323e4567-e89b-12d3-a456-426614174002"
]

response = requests.delete(
    f"{BASE_URL}/questions",
    json={"question_ids": question_ids}
)
print(response.json())
```

**Success Response (200) - All Found:**

```json
{
  "status": "success",
  "message": "Successfully deleted 3 question(s)",
  "deleted_count": 3,
  "requested_count": 3
}
```

**Success Response (200) - Some Not Found:**

```json
{
  "status": "success",
  "message": "Successfully deleted 2 question(s), 1 question(s) not found",
  "deleted_count": 2,
  "requested_count": 3,
  "not_found_ids": [
    "323e4567-e89b-12d3-a456-426614174002"
  ]
}
```

**Error Response (400 - Empty List):**

```json
{
  "detail": "question_ids list cannot be empty"
}
```

---

## Testing

The test suite has been updated with functions to test these new endpoints. You can find them in `test_extraction_api.py`:

### Test Single Delete

```python
from test_extraction_api import test_delete_single_question

# Delete a single question
test_delete_single_question("123e4567-e89b-12d3-a456-426614174000")
```

### Test Multiple Delete

```python
from test_extraction_api import test_delete_multiple_questions

# Delete multiple questions
question_ids = [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-a456-426614174001"
]
test_delete_multiple_questions(question_ids)
```

### Running Full Test Suite

```bash
python test_extraction_api.py
```

**Note:** The delete tests are commented out by default to prevent accidental data deletion. Uncomment them in the `main()` function if you want to test the delete functionality.

---

## Use Cases

### 1. Remove a Specific Question

When you identify a question that was extracted incorrectly or is duplicate:

```python
# Get the question ID from the list endpoint
questions = requests.get(f"{BASE_URL}/questions?limit=10").json()
question_id = questions[0]['id']

# Delete it
requests.delete(f"{BASE_URL}/questions/{question_id}")
```

### 2. Bulk Delete Questions from a Specific File

```python
# Get all questions from a specific file
questions = requests.get(
    f"{BASE_URL}/questions",
    params={"file_name": "math_chapter1.pdf"}
).json()

# Extract question IDs
question_ids = [q['id'] for q in questions]

# Delete them all at once
requests.delete(
    f"{BASE_URL}/questions",
    json={"question_ids": question_ids}
)
```

### 3. Delete Questions by Subject or Class

```python
# Get all questions from a specific subject and class
questions = requests.get(
    f"{BASE_URL}/questions",
    params={
        "subject_name": "الرياضيات",
        "class_name": "الصف الثاني عشر"
    }
).json()

# Extract question IDs
question_ids = [q['id'] for q in questions]

# Delete them
requests.delete(
    f"{BASE_URL}/questions",
    json={"question_ids": question_ids}
)
```

---

## Important Notes

⚠️ **Warning: These are destructive operations!**

- Deleted questions **cannot be recovered** (unless you have database backups)
- Always verify the question IDs before deleting
- Consider implementing a soft-delete mechanism in production environments
- For testing purposes, consider using a separate test database

### Best Practices

1. **Always verify before deleting**: Use the `GET /questions/{question_id}` endpoint to verify the question before deleting it
2. **Log deletions**: The API logs all deletion attempts for audit purposes
3. **Use batch deletes carefully**: When deleting multiple questions, ensure you have the correct IDs
4. **Handle partial failures**: When batch deleting, check the `not_found_ids` field in the response

---

## Error Handling

All delete endpoints return appropriate HTTP status codes:

- **200**: Success
- **400**: Bad request (e.g., empty question_ids list)
- **404**: Question not found (single delete only)
- **500**: Server error (database errors, etc.)

Example error handling in Python:

```python
try:
    response = requests.delete(f"{BASE_URL}/questions/{question_id}")
    response.raise_for_status()
    print(f"Deleted successfully: {response.json()}")
except requests.exceptions.HTTPError as e:
    if response.status_code == 404:
        print(f"Question not found: {question_id}")
    else:
        print(f"Error: {e}")
```

---

## Database Impact

- Questions are permanently removed from the `questions` table
- Foreign key relationships (if any) should be handled appropriately
- Database transactions ensure atomicity (all or nothing for multiple deletes)
- Failed deletions trigger a rollback to maintain data integrity

---

## Future Enhancements

Possible improvements for future versions:

1. **Soft Delete**: Mark questions as deleted instead of removing them
2. **Batch Delete by Filters**: Delete all questions matching certain criteria without fetching IDs first
3. **Undo Functionality**: Temporary recovery window for deleted questions
4. **Audit Trail**: Track who deleted what and when
5. **Rate Limiting**: Prevent accidental mass deletions

