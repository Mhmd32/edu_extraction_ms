# Multiple Choice Options Feature

## Overview

The Question extraction system has been enhanced to automatically extract and store multiple choice options for questions. When the LLM identifies a question as "Multiple Choice", it will now extract up to 6 options and store them in dedicated fields.

---

## 🎯 What's New

### Database Schema Changes

Added 6 new fields to the `Question` model:

- `option1` - First option (TEXT, nullable)
- `option2` - Second option (TEXT, nullable)
- `option3` - Third option (TEXT, nullable)
- `option4` - Fourth option (TEXT, nullable)
- `option5` - Fifth option (TEXT, nullable)
- `option6` - Sixth option (TEXT, nullable)

### LLM Extraction Enhancement

The OpenAI prompt has been updated to:
1. Detect multiple choice questions
2. Extract all available options in order
3. Preserve formatting and symbols (mathematical, chemical, etc.)
4. Store options in the correct option fields (option1-option6)

---

## 📋 How It Works

### 1. Question Type Detection

When the LLM analyzes content, it identifies:
- **Multiple Choice** questions → Extracts options
- **True/False** questions → May use option1 and option2 for True/False
- **Other types** → Option fields remain NULL

### 2. Option Extraction

For a Multiple Choice question like:

```
ما هو ناتج √16 ؟
أ) 2
ب) 4
ج) 8
د) 16
```

The LLM will extract:
- `question`: "ما هو ناتج √16 ؟"
- `question_type`: "Multiple Choice"
- `option1`: "أ) 2"
- `option2`: "ب) 4"
- `option3`: "ج) 8"
- `option4`: "د) 16"
- `option5`: NULL
- `option6`: NULL

### 3. Symbol Preservation

Options maintain all original formatting:
- Mathematical symbols: √, ∫, ∑, π, ², ³
- Chemical formulas: H₂O, CO₂, Fe³⁺
- Arabic numbering: أ، ب، ج، د
- English letters: a, b, c, d
- Numbers: 1, 2, 3, 4

---

## 🔧 Technical Implementation

### Database Model (models.py)

```python
class Question(SQLModel, table=True):
    # ... existing fields ...
    
    # Multiple choice options
    option1: typing.Optional[str] = Field(default=None)
    option2: typing.Optional[str] = Field(default=None)
    option3: typing.Optional[str] = Field(default=None)
    option4: typing.Optional[str] = Field(default=None)
    option5: typing.Optional[str] = Field(default=None)
    option6: typing.Optional[str] = Field(default=None)
    
    # ... other fields ...
```

### API Response Model (app.py)

```python
class QuestionResponse(BaseModel):
    # ... existing fields ...
    
    option1: Optional[str] = None
    option2: Optional[str] = None
    option3: Optional[str] = None
    option4: Optional[str] = None
    option5: Optional[str] = None
    option6: Optional[str] = None
    
    # ... other fields ...
```

### LLM Prompt Enhancement

The Arabic prompt now includes:

```
7. **للأسئلة من نوع "Multiple Choice": استخرج الخيارات بالترتيب وضعها في حقول option1, option2, option3, option4, option5, option6**
   - استخرج الخيارات كما هي مع الحفاظ على الرموز والترقيم (أ، ب، ج، د) أو (1، 2، 3، 4) أو (a، b، c، d)
   - إذا كان هناك أقل من 6 خيارات، اترك الحقول الزائدة فارغة
   - احفظ كل خيار كنص كامل مع الرموز الرياضية أو العلمية
```

---

## 📊 Database Migration

### If Using Existing Database

You need to add the new columns to your existing `questions` table:

```sql
ALTER TABLE questions ADD COLUMN option1 TEXT;
ALTER TABLE questions ADD COLUMN option2 TEXT;
ALTER TABLE questions ADD COLUMN option3 TEXT;
ALTER TABLE questions ADD COLUMN option4 TEXT;
ALTER TABLE questions ADD COLUMN option5 TEXT;
ALTER TABLE questions ADD COLUMN option6 TEXT;
```

### If Creating New Database

The new fields will be automatically created when you run:

```python
from fastapi_app.models import create_db_and_tables
create_db_and_tables()
```

---

## 🚀 API Usage Examples

### Example 1: Get Multiple Choice Questions

```python
import requests

# Get all multiple choice questions
response = requests.get(
    "http://localhost:8000/questions",
    params={"question_type": "Multiple Choice", "limit": 10}
)

questions = response.json()

for q in questions:
    print(f"Question: {q['question']}")
    print(f"Options:")
    if q['option1']:
        print(f"  1. {q['option1']}")
    if q['option2']:
        print(f"  2. {q['option2']}")
    if q['option3']:
        print(f"  3. {q['option3']}")
    if q['option4']:
        print(f"  4. {q['option4']}")
    if q['option5']:
        print(f"  5. {q['option5']}")
    if q['option6']:
        print(f"  6. {q['option6']}")
    print(f"Correct Answer: {q['correct_answer']}\n")
```

### Example 2: API Response Structure

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "file_name": "math_chapter1.pdf",
  "subject_name": "الرياضيات",
  "lesson_title": "الجذور التربيعية",
  "class_name": "الصف الثاني عشر",
  "specialization": "علمي",
  "question": "ما هو ناتج √16 ؟",
  "question_type": "Multiple Choice",
  "question_difficulty": "Easy",
  "page_number": "15",
  "option1": "أ) 2",
  "option2": "ب) 4",
  "option3": "ج) 8",
  "option4": "د) 16",
  "option5": null,
  "option6": null,
  "answer_steps": null,
  "correct_answer": "ب) 4",
  "uploaded_by": "teacher1",
  "updated_by": null,
  "created_at": "2025-11-28T10:30:00",
  "updated_at": "2025-11-28T10:30:00"
}
```

### Example 3: Extract Questions with Options

When you upload a PDF with multiple choice questions:

```python
import requests

# Upload PDF for extraction
with open("textbook.pdf", "rb") as f:
    files = {"file": ("textbook.pdf", f, "application/pdf")}
    data = {
        "subject_name": "الرياضيات",
        "class_name": "الصف الثاني عشر",
        "specialization": "علمي",
        "uploaded_by": "teacher1"
    }
    
    response = requests.post(
        "http://localhost:8000/extract",
        files=files,
        data=data
    )

print(response.json())
```

The extracted multiple choice questions will automatically include their options in the database.

---

## ✨ Features

### ✅ Automatic Detection
- LLM automatically identifies multiple choice questions
- No manual configuration needed

### ✅ Flexible Option Count
- Supports 2-6 options
- Unused option fields are left NULL

### ✅ Symbol Preservation
- All mathematical and scientific symbols preserved
- Original formatting maintained

### ✅ Multi-Language Support
- Arabic options: أ، ب، ج، د
- English options: a, b, c, d
- Numeric options: 1, 2, 3, 4

### ✅ Backward Compatible
- Existing questions without options remain valid
- All option fields are nullable

---

## 🎓 Use Cases

### 1. Quiz Generation
Extract multiple choice questions and display them with options in a quiz interface.

### 2. Study Materials
Create study guides with questions and their options.

### 3. Question Banks
Build comprehensive question banks organized by options.

### 4. Assessment Tools
Generate assessments with properly formatted multiple choice questions.

---

## 🔍 Querying Questions with Options

### Get Questions with Options

```python
import requests

# Get all questions that have options
response = requests.get("http://localhost:8000/questions?limit=100")
questions = response.json()

# Filter questions that have at least one option
questions_with_options = [
    q for q in questions 
    if q.get('option1') is not None
]

print(f"Found {len(questions_with_options)} questions with options")
```

### Filter by Subject and Type

```python
# Get math multiple choice questions
response = requests.get(
    "http://localhost:8000/questions",
    params={
        "subject_name": "الرياضيات",
        "question_type": "Multiple Choice",
        "limit": 50
    }
)

questions = response.json()
```

---

## 📝 Important Notes

### 1. Option Order
Options are stored in the order they appear in the source material. The LLM preserves:
- Original numbering (أ، ب، ج or 1، 2، 3)
- Original text
- All formatting

### 2. NULL Values
If a question has fewer than 6 options, the remaining option fields will be NULL. This is normal and expected.

### 3. Non-Multiple Choice Questions
For questions that are not "Multiple Choice", all option fields will be NULL.

### 4. Correct Answer
The `correct_answer` field may contain:
- The letter/number of the correct option (e.g., "ب" or "2")
- The full text of the correct option
- A description of the answer

---

## 🧪 Testing

### Test Multiple Choice Extraction

```python
# Upload a PDF with multiple choice questions
# Check the extracted questions
questions = requests.get(
    "http://localhost:8000/questions?question_type=Multiple Choice&limit=5"
).json()

# Verify options are extracted
for q in questions:
    assert q['question_type'] == 'Multiple Choice'
    assert q['option1'] is not None or q['option2'] is not None
    print(f"✅ Question has {sum(1 for i in range(1,7) if q.get(f'option{i}'))} options")
```

---

## 🔧 Troubleshooting

### Options Not Extracted

**Problem**: Multiple choice questions have NULL options

**Solutions**:
1. Verify the PDF text is clear and readable
2. Check that options are formatted consistently (أ، ب، ج)
3. Ensure the question type is correctly identified as "Multiple Choice"

### Wrong Option Count

**Problem**: Some options are missing or extra

**Solutions**:
1. Review the source PDF formatting
2. Check for option text that spans multiple lines
3. Verify option numbering is consistent

### Symbol Issues

**Problem**: Mathematical symbols in options not preserved

**Solutions**:
1. Ensure PDF extraction maintains symbols
2. Check Azure Document Intelligence output
3. Verify UTF-8 encoding throughout the pipeline

---

## 📚 Files Modified

1. **src/fastapi_app/models.py**
   - Added option1-option6 fields to Question model

2. **src/fastapi_app/app.py**
   - Updated OpenAI prompt to extract options
   - Updated store_questions_in_db to handle option fields
   - Updated QuestionResponse model to include option fields

---

## 🎯 Next Steps

1. **Database Migration**: Run the ALTER TABLE commands on existing databases
2. **Test Extraction**: Upload PDFs with multiple choice questions
3. **Verify API**: Check that GET /questions returns option fields
4. **Frontend Integration**: Update UI to display options for multiple choice questions

---

**Implementation Date**: 2025-11-28  
**Status**: ✅ Complete and Ready to Use

