# Question Extraction API Documentation

This document describes the question extraction functionality using Azure Document Intelligence and OpenAI.

## Environment Variables

Add these environment variables to your Azure Web App or local `.env` file:

```env
# Azure Document Intelligence
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOC_INTELLIGENCE_KEY=your_azure_doc_intelligence_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o

# Default Values
DEFAULT_UPLOADED_BY=system
```

## API Endpoints

### 1. Extract Questions from PDF

**Endpoint:** `POST /extract`

**Description:** Extracts questions from a PDF file using Azure Document Intelligence and OpenAI.

**Parameters:**
- `file` (required): PDF file to upload
- `subject_name` (required): Subject name (e.g., "الرياضيات", "الفيزياء")
- `class_name` (optional): Class name (e.g., "الصف الثاني عشر")
- `specialization` (optional): Specialization (e.g., "علمي", "أدبي")
- `uploaded_by` (required): Username of the uploader
- `updated_by` (optional): Username of the updater
- `metadata` (optional): JSON string containing any of the above fields

**Example using cURL:**

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@textbook.pdf" \
  -F "subject_name=الرياضيات" \
  -F "class_name=الصف الثاني عشر" \
  -F "specialization=علمي" \
  -F "uploaded_by=admin"
```

**Example using Python:**

```python
import requests

url = "http://localhost:8000/extract"
files = {"file": open("textbook.pdf", "rb")}
data = {
    "subject_name": "الرياضيات",
    "class_name": "الصف الثاني عشر",
    "specialization": "علمي",
    "uploaded_by": "admin"
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Response:**

```json
{
  "status": "success",
  "message": "Processed 10 page(s); stored 45 question(s).",
  "summary": {
    "total_pages_detected": 10,
    "pages_with_content": 10,
    "pages_skipped": 0,
    "questions_stored": 45,
    "pages": [
      {
        "page_number": 1,
        "questions_extracted": 5,
        "status": "processed"
      }
    ]
  }
}
```

### 2. List Questions

**Endpoint:** `GET /questions`

**Description:** Retrieve stored questions with optional filters.

**Query Parameters:**
- `subject_name` (optional): Filter by subject
- `class_name` (optional): Filter by class
- `specialization` (optional): Filter by specialization
- `lesson_title` (optional): Filter by lesson title (partial match)
- `question_type` (optional): Filter by type (Descriptive, Multiple Choice, etc.)
- `question_difficulty` (optional): Filter by difficulty (Easy, Medium, Hard)
- `limit` (optional): Number of results (default: 100, max: 500)
- `offset` (optional): Pagination offset (default: 0)

**Example:**

```bash
curl "http://localhost:8000/questions?subject_name=الرياضيات&limit=10"
```

**Response:**

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "file_name": "textbook.pdf",
    "subject_name": "الرياضيات",
    "lesson_title": "التفاضل والتكامل",
    "class_name": "الصف الثاني عشر",
    "specialization": "علمي",
    "question": "احسب ∫ x² dx",
    "question_type": "Descriptive",
    "question_difficulty": "Medium",
    "page_number": "15",
    "answer_steps": "نستخدم قاعدة القوة...",
    "correct_answer": "x³/3 + C",
    "uploaded_by": "admin",
    "updated_by": null,
    "created_at": "2025-11-20T10:30:00",
    "updated_at": "2025-11-20T10:30:00"
  }
]
```

## User Management Endpoints

### 3. Create User

**Endpoint:** `POST /users`

**Request Body:**

```json
{
  "username": "teacher1",
  "password": "securepassword",
  "display_name": "أستاذ أحمد",
  "is_admin": false,
  "is_active": true
}
```

### 4. List Users

**Endpoint:** `GET /users?limit=10&offset=0`

### 5. Update User

**Endpoint:** `PUT /users/{user_id}`

**Request Body:**

```json
{
  "display_name": "أستاذ أحمد المحدث",
  "is_admin": true
}
```

### 6. Login

**Endpoint:** `POST /login`

**Request Body:**

```json
{
  "username": "teacher1",
  "password": "securepassword"
}
```

## Database Schema

### Users Table

- `id`: UUID (primary key)
- `username`: VARCHAR(100) (unique, indexed)
- `display_name`: VARCHAR(200)
- `password_hash`: VARCHAR(64) (SHA-256)
- `is_admin`: BOOLEAN (default: false)
- `is_active`: BOOLEAN (default: true)
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

### Questions Table

- `id`: UUID (primary key)
- `file_name`: VARCHAR(500)
- `subject_name`: VARCHAR(200)
- `lesson_title`: VARCHAR(500)
- `class_name`: VARCHAR(100)
- `specialization`: VARCHAR(200)
- `question`: TEXT
- `question_type`: VARCHAR(50)
- `question_difficulty`: VARCHAR(20)
- `page_number`: VARCHAR(20)
- `answer_steps`: TEXT
- `correct_answer`: TEXT
- `uploaded_by`: VARCHAR(100)
- `updated_by`: VARCHAR(100)
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

## Question Types

- `Descriptive`: Essay or descriptive questions
- `Multiple Choice`: Multiple choice questions
- `True/False`: True or false questions
- `Fill in the blank`: Fill in the blank questions
- `Short Answer`: Short answer questions

## Question Difficulty Levels

- `Easy`: Easy questions
- `Medium`: Medium difficulty questions
- `Hard`: Hard questions

## Setup Instructions

1. Install dependencies:
```bash
pip install -e .
```

2. Create `.env` file with required environment variables (see above)

3. Initialize database:
```bash
python -m fastapi_app.seed_data
```

4. Run the application:
```bash
uvicorn fastapi_app.app:app --reload
```

5. Access API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Notes

- PDF files must be in a supported format for Azure Document Intelligence
- The extraction process uses GPT-4o by default for question extraction
- Mathematical symbols (√, ∫, ∑, etc.) and chemical formulas (H₂O, CO₂) are preserved
- Arabic content is fully supported
- Questions are automatically deduplicated by UUID
- Temp files are automatically cleaned up after processing

