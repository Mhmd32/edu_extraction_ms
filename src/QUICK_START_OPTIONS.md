# 🚀 Quick Start: Multiple Choice Options

## What's New?

Your Question extraction system now automatically extracts and stores multiple choice options!

---

## 🎯 Quick Setup (3 Steps)

### Step 1: Migrate Your Database

```bash
cd src
python migrate_add_options.py
```

This adds 6 new columns (option1-option6) to your questions table.

---

### Step 2: Extract Questions

Upload a PDF with multiple choice questions:

```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@your_textbook.pdf" \
  -F "subject_name=الرياضيات" \
  -F "class_name=الصف الثاني عشر" \
  -F "uploaded_by=teacher1"
```

Or use Python:

```python
import requests

with open("textbook.pdf", "rb") as f:
    files = {"file": ("textbook.pdf", f, "application/pdf")}
    data = {
        "subject_name": "الرياضيات",
        "class_name": "الصف الثاني عشر",
        "uploaded_by": "teacher1"
    }
    
    response = requests.post(
        "http://localhost:8000/extract",
        files=files,
        data=data
    )
    print(response.json())
```

**The LLM will automatically extract options for Multiple Choice questions!**

---

### Step 3: Retrieve Questions with Options

```python
import requests

# Get multiple choice questions
response = requests.get(
    "http://localhost:8000/questions",
    params={"question_type": "Multiple Choice", "limit": 5}
)

questions = response.json()

# Display with options
for q in questions:
    print(f"\nQuestion: {q['question']}")
    print("Options:")
    for i in range(1, 7):
        option = q.get(f'option{i}')
        if option:
            print(f"  {option}")
    print(f"Answer: {q.get('correct_answer', 'N/A')}")
```

---

## 🧪 Test It

```bash
python test_options_feature.py
```

This will:
- ✅ Verify option fields exist in API responses
- ✅ Get multiple choice questions
- ✅ Display questions in quiz format
- ✅ Show statistics about questions with options

---

## 📊 API Response Format

### Before:
```json
{
  "question": "ما هو ناتج √16 ؟",
  "question_type": "Multiple Choice",
  "correct_answer": "4"
}
```

### After (NEW):
```json
{
  "question": "ما هو ناتج √16 ؟",
  "question_type": "Multiple Choice",
  "option1": "أ) 2",
  "option2": "ب) 4",
  "option3": "ج) 8",
  "option4": "د) 16",
  "option5": null,
  "option6": null,
  "correct_answer": "4"
}
```

---

## 💡 Key Points

### Automatic Extraction
- ✅ Works automatically for Multiple Choice questions
- ✅ No configuration needed
- ✅ LLM extracts options in order

### Flexible
- ✅ Supports 2-6 options
- ✅ Unused options are NULL
- ✅ Works with any numbering (أ/ب/ج, 1/2/3, a/b/c)

### Symbol Preservation
- ✅ Mathematical: √, ∫, ∑, π, ²
- ✅ Chemical: H₂O, CO₂, Fe³⁺
- ✅ All formatting preserved

### Backward Compatible
- ✅ Existing questions work fine
- ✅ Old questions have NULL options
- ✅ No breaking changes

---

## 🎓 Usage Examples

### Display as Quiz

```python
def display_quiz(question):
    print(f"\n{question['question']}")
    print(f"Difficulty: {question['question_difficulty']}\n")
    
    # Show options
    options = []
    for i in range(1, 7):
        opt = question.get(f'option{i}')
        if opt:
            options.append(opt)
            print(f"  {opt}")
    
    return options

# Get and display
response = requests.get(
    "http://localhost:8000/questions?question_type=Multiple Choice&limit=5"
)

for q in response.json():
    display_quiz(q)
```

### Filter Questions with Options

```python
# Get all questions
all_questions = requests.get(
    "http://localhost:8000/questions?limit=100"
).json()

# Filter those with options
questions_with_options = [
    q for q in all_questions
    if any(q.get(f'option{i}') for i in range(1, 7))
]

print(f"Found {len(questions_with_options)} questions with options")
```

### Generate Study Material

```python
def generate_study_guide(subject):
    response = requests.get(
        "http://localhost:8000/questions",
        params={
            "subject_name": subject,
            "question_type": "Multiple Choice"
        }
    )
    
    questions = response.json()
    
    print(f"# Study Guide: {subject}\n")
    
    for i, q in enumerate(questions, 1):
        print(f"## Question {i}")
        print(f"{q['question']}\n")
        
        for j in range(1, 7):
            opt = q.get(f'option{j}')
            if opt:
                print(f"{opt}")
        
        print(f"\n**Answer:** {q.get('correct_answer', 'N/A')}\n")
        print("---\n")

generate_study_guide("الرياضيات")
```

---

## 📚 Full Documentation

For complete details, see:
- **OPTIONS_IMPLEMENTATION_SUMMARY.md** - Complete overview
- **OPTIONS_FIELDS_FEATURE.md** - Detailed documentation
- **migrate_add_options.py** - Database migration script
- **test_options_feature.py** - Test suite

---

## ⚡ Quick Commands

```bash
# Migrate database
python migrate_add_options.py

# Test feature
python test_options_feature.py

# Get multiple choice questions
curl "http://localhost:8000/questions?question_type=Multiple%20Choice"

# Extract PDF
curl -X POST "http://localhost:8000/extract" \
  -F "file=@textbook.pdf" \
  -F "subject_name=Math" \
  -F "uploaded_by=teacher"
```

---

## ✅ Status

**Implementation**: ✅ Complete  
**Testing**: ✅ Ready  
**Documentation**: ✅ Complete  
**Migration**: ✅ Available  

**You're all set! Start extracting multiple choice questions with options! 🎉**

