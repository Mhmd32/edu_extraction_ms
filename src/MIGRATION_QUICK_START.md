# 🚀 Quick Start: Database Migration

## What Changed

The `migrate_add_options.py` script now works like `seed_data.py`:

✅ **Imports from models.py** - Uses the Question model directly  
✅ **Uses SQLAlchemy** - No raw SQL, just SQLAlchemy schema operations  
✅ **Same engine** - Uses the engine from models.py (same connection as your app)  
✅ **Safe & Idempotent** - Adds only missing columns, safe to run multiple times  

---

## 🎯 How to Use

### Just like seed_data.py, run:

```bash
# Local
cd src
python migrate_add_options.py
```

```bash
# On Azure
python3 migrate_add_options.py
```

That's it! 🎉

---

## 📋 What It Does

1. **Imports** `Question` model and `engine` from `models.py`
2. **Inspects** the database to see which columns exist
3. **Adds** missing option columns (option1-option6)
4. **Verifies** all columns were added successfully

---

## ✨ Key Differences from Old Version

| Before | After |
|--------|-------|
| Raw SQL strings | SQLAlchemy Column/AddColumn |
| Manual DB connection | Uses engine from models.py |
| Independent script | Imports from models.py |
| Complex setup | Simple like seed_data.py |

---

## 🔧 Code Overview

### Old Approach (Raw SQL)
```python
# Old way - raw SQL
alter_query = text(f"ALTER TABLE questions ADD COLUMN {column_name} TEXT;")
conn.execute(alter_query)
```

### New Approach (SQLAlchemy)
```python
# New way - SQLAlchemy schema operations
from fastapi_app.models import Question, engine
from sqlalchemy import Column, Text
from sqlalchemy.schema import AddColumn

column = Column(column_name, Text, nullable=True)
with engine.begin() as conn:
    conn.execute(AddColumn('questions', column))
```

**Benefits:**
- ✅ Consistent with models.py definitions
- ✅ Type-safe with SQLAlchemy
- ✅ Database-agnostic (works with PostgreSQL, MySQL, etc.)
- ✅ Follows the same pattern as seed_data.py

---

## 📝 Example Output

```
============================================================
Database Migration: Add Option Fields
Using SQLAlchemy schema from models.py
============================================================

Testing database connection...
✅ Database connection successful!

Starting migration: Adding option columns to questions table...
Reading schema from Question model in models.py

Found 15 existing columns in questions table
  ✅ Added column 'option1' (TEXT, nullable)
  ✅ Added column 'option2' (TEXT, nullable)
  ✅ Added column 'option3' (TEXT, nullable)
  ✅ Added column 'option4' (TEXT, nullable)
  ✅ Added column 'option5' (TEXT, nullable)
  ✅ Added column 'option6' (TEXT, nullable)

============================================================
Migration completed!
  Columns added: 6
  Columns skipped (already exist): 0
============================================================

✨ Your database has been successfully updated!
The questions table now supports multiple choice options.

Verifying migration...
  ✅ option1: EXISTS
  ✅ option2: EXISTS
  ✅ option3: EXISTS
  ✅ option4: EXISTS
  ✅ option5: EXISTS
  ✅ option6: EXISTS

✅ All option columns verified successfully!

============================================================
Migration completed successfully! 🎉
============================================================

📝 Summary:
  - New columns added: 6
  - Existing columns skipped: 0
  - Total option fields: 6

🎓 Next steps:
  1. Extract PDFs with multiple choice questions
  2. Options will be automatically extracted by the LLM
  3. Test with: python test_options_feature.py
```

---

## 🔄 Comparison with seed_data.py

### seed_data.py
```python
from fastapi_app.models import create_db_and_tables

if __name__ == "__main__":
    create_db_and_tables()  # Creates missing tables
```

### migrate_add_options.py (NEW)
```python
from fastapi_app.models import Question, engine
from sqlalchemy import Column, Text, inspect
from sqlalchemy.schema import AddColumn

def add_missing_columns(engine):
    # Adds missing columns to existing table
    inspector = inspect(engine)
    existing = {col['name'] for col in inspector.get_columns('questions')}
    
    for col_name in ['option1', 'option2', ...]:
        if col_name not in existing:
            column = Column(col_name, Text, nullable=True)
            with engine.begin() as conn:
                conn.execute(AddColumn('questions', column))

if __name__ == "__main__":
    main()  # Adds missing columns
```

**Both follow the same pattern!**

---

## ✅ Requirements

Same as your FastAPI app:

- ✅ `.env` file with database credentials (local)
- ✅ Azure environment variables (on Azure)
- ✅ Questions table already exists (created by seed_data.py)

---

## 🛠️ Troubleshooting

### "Module 'fastapi_app' not found"

**Fix**: Make sure you're in the `src` directory:
```bash
cd src
python migrate_add_options.py
```

### "Questions table does not exist"

**Fix**: Create tables first:
```bash
python3 src/fastapi_app/seed_data.py
```

### "Permission denied to alter table"

**Fix**: Check database user permissions or use admin credentials

---

## 🎓 After Migration

1. **Test the migration**:
   ```bash
   python test_options_feature.py
   ```

2. **Extract PDFs with multiple choice questions**:
   ```bash
   curl -X POST "http://localhost:8000/extract" \
     -F "file=@textbook.pdf" \
     -F "subject_name=Math" \
     -F "uploaded_by=teacher"
   ```

3. **Get questions with options**:
   ```bash
   curl "http://localhost:8000/questions?question_type=Multiple%20Choice"
   ```

---

## 📚 Full Documentation

For detailed information, see:
- **MIGRATION_GUIDE.md** - Complete migration guide
- **OPTIONS_IMPLEMENTATION_SUMMARY.md** - Full feature overview
- **QUICK_START_OPTIONS.md** - Quick start for using options

---

## ✨ Summary

The migration script now:
- ✅ Works like `seed_data.py` (imports from models.py)
- ✅ Uses SQLAlchemy (no raw SQL)
- ✅ Is idempotent (safe to run multiple times)
- ✅ Preserves all existing data
- ✅ Follows the same pattern as your existing scripts

**Just run it like you run seed_data.py!** 🚀

