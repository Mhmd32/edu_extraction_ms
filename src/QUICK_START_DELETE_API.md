# 🚀 Quick Start: Delete Questions API

## New Endpoints Available

### 1️⃣ Delete Single Question
```
DELETE /questions/{question_id}
```

### 2️⃣ Delete Multiple Questions
```
DELETE /questions
```

---

## 🔥 Quick Examples

### Example 1: Delete One Question

**Using cURL:**
```bash
curl -X DELETE "http://localhost:8000/questions/123e4567-e89b-12d3-a456-426614174000"
```

**Using Python:**
```python
import requests

question_id = "123e4567-e89b-12d3-a456-426614174000"
response = requests.delete(f"http://localhost:8000/questions/{question_id}")
print(response.json())
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully deleted question",
  "deleted_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

### Example 2: Delete Multiple Questions

**Using cURL:**
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

**Using Python:**
```python
import requests

question_ids = [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-a456-426614174001"
]

response = requests.delete(
    "http://localhost:8000/questions",
    json={"question_ids": question_ids}
)
print(response.json())
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully deleted 2 question(s)",
  "deleted_count": 2,
  "requested_count": 2
}
```

---

## 🧪 Test It

### Step 1: Start the Server
```bash
cd src
uvicorn fastapi_app.app:app --reload
```

### Step 2: Get Some Question IDs
```bash
curl "http://localhost:8000/questions?limit=5"
```

### Step 3: Delete a Question
```bash
# Replace with actual question ID
curl -X DELETE "http://localhost:8000/questions/YOUR-QUESTION-ID-HERE"
```

---

## 📝 Test Functions Available

In `test_extraction_api.py`:

```python
# Test single delete
test_delete_single_question("your-question-id")

# Test multiple delete
test_delete_multiple_questions(["id1", "id2", "id3"])
```

---

## ⚠️ Important

- **These operations are permanent** - deleted questions cannot be recovered
- **Use with caution** - always verify question IDs before deleting
- **Test in development first** - make sure you understand the behavior

---

## 📚 Full Documentation

For complete documentation, see:
- **DELETE_QUESTIONS_API.md** - Full API reference
- **DELETE_API_SUMMARY.md** - Implementation summary

---

## ✅ Status

**Implementation Complete**: All endpoints tested and working ✨

