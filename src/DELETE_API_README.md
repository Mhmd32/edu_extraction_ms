# Delete Questions API Documentation

## Overview

The Delete Questions API provides a secure way to delete questions from the database with password-protected authentication.

## Authentication

**All delete operations require password authentication via HTTP header:**

```
X-Delete-Password: Mhmd@123
```

❌ **Requests without this header or with incorrect password will be rejected with 401 Unauthorized.**

## Endpoint

```
DELETE /questions
```

## Delete Options

### Option 1: Delete by Question ID

Delete a specific question using its UUID.

**Parameters:**
- `question_id` (string): The UUID of the question to delete

**Example:**
```bash
curl -X DELETE "http://localhost:8000/questions?question_id=123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Delete-Password: Mhmd@123"
```

**Response:**
```json
{
  "status": "success",
  "message": "Question deleted successfully",
  "deleted_count": 1
}
```

### Option 2: Delete by Filters

Delete all questions matching specific criteria.

**Available Filters:**
- `subject_name` (string): Subject name (e.g., "الرياضيات")
- `class_name` (string): Class name (e.g., "الصف الثاني عشر")
- `specialization` (string): Specialization (e.g., "علمي")
- `lesson_title` (string): Lesson title (partial match supported)

**Example 1: Delete all math questions**
```bash
curl -X DELETE "http://localhost:8000/questions?subject_name=الرياضيات" \
  -H "X-Delete-Password: Mhmd@123"
```

**Example 2: Delete questions for specific class and subject**
```bash
curl -X DELETE "http://localhost:8000/questions?subject_name=الفيزياء&class_name=الصف الثاني عشر" \
  -H "X-Delete-Password: Mhmd@123"
```

**Example 3: Delete questions from a specific lesson**
```bash
curl -X DELETE "http://localhost:8000/questions?lesson_title=التفاضل" \
  -H "X-Delete-Password: Mhmd@123"
```

**Response:**
```json
{
  "status": "success",
  "message": "Questions deleted successfully",
  "deleted_count": 25,
  "filters": {
    "subject_name": "الرياضيات",
    "class_name": "الصف الثاني عشر",
    "specialization": null,
    "lesson_title": null
  }
}
```

### Option 3: Delete All Questions

⚠️ **USE WITH EXTREME CAUTION** - This will delete ALL questions from the database.

**Parameters:**
- `delete_all=true` (boolean): Must be set to true

**Example:**
```bash
curl -X DELETE "http://localhost:8000/questions?delete_all=true" \
  -H "X-Delete-Password: Mhmd@123"
```

**Response:**
```json
{
  "status": "success",
  "message": "All questions deleted",
  "deleted_count": 150
}
```

## Python Examples

### Using requests library

```python
import requests

BASE_URL = "http://localhost:8000"
PASSWORD = "Mhmd@123"

# Delete by ID
def delete_question_by_id(question_id):
    response = requests.delete(
        f"{BASE_URL}/questions",
        params={"question_id": question_id},
        headers={"X-Delete-Password": PASSWORD}
    )
    return response.json()

# Delete by subject
def delete_by_subject(subject_name):
    response = requests.delete(
        f"{BASE_URL}/questions",
        params={"subject_name": subject_name},
        headers={"X-Delete-Password": PASSWORD}
    )
    return response.json()

# Delete by multiple filters
def delete_by_filters(subject, class_name):
    response = requests.delete(
        f"{BASE_URL}/questions",
        params={
            "subject_name": subject,
            "class_name": class_name
        },
        headers={"X-Delete-Password": PASSWORD}
    )
    return response.json()

# Delete all (use with caution!)
def delete_all_questions():
    response = requests.delete(
        f"{BASE_URL}/questions",
        params={"delete_all": True},
        headers={"X-Delete-Password": PASSWORD}
    )
    return response.json()

# Usage examples
result = delete_question_by_id("123e4567-e89b-12d3-a456-426614174000")
print(f"Deleted {result['deleted_count']} question(s)")

result = delete_by_subject("الرياضيات")
print(f"Deleted {result['deleted_count']} math questions")
```

### Using httpx (async)

```python
import httpx
import asyncio

async def delete_questions_async(subject_name):
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            "http://localhost:8000/questions",
            params={"subject_name": subject_name},
            headers={"X-Delete-Password": "Mhmd@123"}
        )
        return response.json()

# Run async
result = asyncio.run(delete_questions_async("الرياضيات"))
print(result)
```

## Response Codes

| Status Code | Description |
|------------|-------------|
| 200 | Questions deleted successfully |
| 401 | Unauthorized - Invalid or missing password |
| 404 | No questions found matching criteria |
| 400 | Bad request - Invalid question_id format |

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Unauthorized: Invalid password"
}
```

### 404 Not Found
```json
{
  "detail": "No questions found matching the criteria"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid question_id format"
}
```

## Security Notes

1. **Password is hardcoded**: `Mhmd@123`
2. Password must be sent in the `X-Delete-Password` header
3. All delete attempts are logged
4. Unauthorized attempts are logged with warning level

## Testing the API

### Interactive API Documentation

Visit the FastAPI Swagger UI to test the delete endpoint interactively:

```
http://localhost:8000/docs
```

1. Navigate to the `DELETE /questions` endpoint
2. Click "Try it out"
3. Add the header: `X-Delete-Password: Mhmd@123`
4. Set your parameters
5. Click "Execute"

### Using Postman

1. Create a new DELETE request
2. URL: `http://localhost:8000/questions?subject_name=الرياضيات`
3. Add Header:
   - Key: `X-Delete-Password`
   - Value: `Mhmd@123`
4. Send the request

## Best Practices

1. **Always backup before deleting**: Consider backing up the database before bulk delete operations
2. **Test with specific filters first**: Use filters to delete smaller subsets before attempting large deletions
3. **Verify count**: Check the `deleted_count` in the response to ensure expected number of deletions
4. **Use delete_all sparingly**: Only use `delete_all=true` when you're absolutely certain
5. **Log review**: Check application logs to verify deletions were performed correctly

## Combining with Other Endpoints

### Delete and Verify Workflow

```bash
# 1. Check how many questions exist
curl "http://localhost:8000/questions?subject_name=الرياضيات"

# 2. Delete the questions
curl -X DELETE "http://localhost:8000/questions?subject_name=الرياضيات" \
  -H "X-Delete-Password: Mhmd@123"

# 3. Verify deletion
curl "http://localhost:8000/questions?subject_name=الرياضيات"
```

### Get Question ID, Then Delete

```bash
# 1. Get question details
curl "http://localhost:8000/questions?subject_name=الرياضيات&limit=1"

# Copy the ID from response, then delete
curl -X DELETE "http://localhost:8000/questions?question_id=PASTE_ID_HERE" \
  -H "X-Delete-Password: Mhmd@123"
```

## Troubleshooting

### Issue: 401 Unauthorized

**Problem:** Password is incorrect or not provided

**Solutions:**
- Verify header name is exactly: `X-Delete-Password`
- Verify password is exactly: `Mhmd@123` (case-sensitive)
- Ensure header is being sent with the request

### Issue: 404 Not Found

**Problem:** No questions match the provided filters

**Solutions:**
- Verify the filter values are correct
- Check spelling of subject names, class names, etc.
- Use GET `/questions` first to verify questions exist

### Issue: Nothing gets deleted

**Problem:** Filters might be too restrictive

**Solutions:**
- Try fewer filters
- Use GET `/questions` with same filters to see what would be deleted
- Check logs for any errors

## Change Password

To change the delete password, update this line in `src/fastapi_app/app.py`:

```python
if password != "Mhmd@123":  # Change this value
```

After changing, redeploy the application.

## Logging

All delete operations are logged:

```
INFO: Authorized delete request received
INFO: Deleting ALL questions  # For delete_all=true
```

Unauthorized attempts:

```
WARNING: Unauthorized delete attempt
```

Check logs with:

```bash
# Azure
az webapp log tail --name your-app-name --resource-group your-resource-group

# Local
# Check terminal output where uvicorn is running
```

## Future Enhancements

Potential improvements for production use:

1. **Database backup before delete**: Automatically create backup
2. **Soft delete**: Mark as deleted instead of removing
3. **Audit trail**: Record who deleted what and when
4. **Undo functionality**: Restore recently deleted questions
5. **Batch delete with confirmation**: Require explicit confirmation for bulk deletes
6. **Role-based access**: Use user authentication instead of shared password
7. **Delete history**: Keep record of all delete operations

---

**Remember:** Deletions are permanent and cannot be undone. Always verify your filters before executing delete operations!

