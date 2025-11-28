# Database Migration Guide: Adding Option Fields

## Overview

The `migrate_add_options.py` script adds the option1-option6 fields to your existing questions table without deleting any data. It works similar to `seed_data.py` by importing from `models.py` and using SQLAlchemy to manage the schema.

---

## 🎯 How It Works

### Similar to seed_data.py

Just like how you used:
```bash
python3 src/fastapi_app/seed_data.py
```

You now use:
```bash
python3 migrate_add_options.py
```

### What It Does

1. **Imports from models.py**: Reads the Question model definition with the new option fields
2. **Inspects Database**: Checks which columns already exist in the questions table
3. **Adds Missing Columns**: Uses SQLAlchemy's AddColumn to add only the missing option fields
4. **Verifies**: Confirms all option columns were added successfully

### Key Differences from Old Approach

| Old Approach | New Approach |
|--------------|--------------|
| Raw SQL ALTER TABLE | SQLAlchemy schema operations |
| Manual connection string parsing | Uses engine from models.py |
| Direct SQL execution | Uses SQLAlchemy Column and AddColumn |
| Independent of models.py | Imports directly from models.py |

---

## 🚀 Usage

### Local Development

```bash
cd src
python migrate_add_options.py
```

### On Azure App Service

```bash
python3 migrate_add_options.py
```

Or via Azure SSH/Console:
```bash
cd /home/site/wwwroot/src
python3 migrate_add_options.py
```

---

## 📋 What Gets Added

The script adds these 6 columns to the `questions` table:

```python
option1: TEXT (nullable)
option2: TEXT (nullable)
option3: TEXT (nullable)
option4: TEXT (nullable)
option5: TEXT (nullable)
option6: TEXT (nullable)
```

All columns are:
- ✅ Nullable (won't break existing data)
- ✅ TEXT type (no length limit)
- ✅ Defined in models.py
- ✅ Added only if they don't exist (idempotent)

---

## 🔧 Requirements

The script uses the same database connection as your FastAPI app:

### Local (.env file)
```
DBUSER=your_username
DBPASS=your_password
DBHOST=localhost
DBNAME=your_database
DBPORT=5432
```

### Azure (Environment Variables)
- `AZURE_POSTGRESQL_CONNECTIONSTRING` (automatically set by Azure)
- Or individual variables: `DBUSER`, `DBPASS`, `DBHOST`, `DBNAME`

---

## 📝 Example Output

### First Run (Adding Columns)

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

### Second Run (Already Migrated)

```
============================================================
Database Migration: Add Option Fields
Using SQLAlchemy schema from models.py
============================================================

Testing database connection...
✅ Database connection successful!

Starting migration: Adding option columns to questions table...
Reading schema from Question model in models.py

Found 21 existing columns in questions table
  ⏭️  Column 'option1' already exists. Skipping.
  ⏭️  Column 'option2' already exists. Skipping.
  ⏭️  Column 'option3' already exists. Skipping.
  ⏭️  Column 'option4' already exists. Skipping.
  ⏭️  Column 'option5' already exists. Skipping.
  ⏭️  Column 'option6' already exists. Skipping.

============================================================
Migration completed!
  Columns added: 0
  Columns skipped (already exist): 6
============================================================

✨ All columns already exist. No changes needed.

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
```

---

## ⚡ Key Features

### 1. Idempotent
- ✅ Safe to run multiple times
- ✅ Skips existing columns
- ✅ No errors if already migrated

### 2. Non-Destructive
- ✅ Never deletes data
- ✅ Only adds missing columns
- ✅ Preserves all existing questions

### 3. Follows models.py
- ✅ Uses Question model definition
- ✅ Same engine/connection as the app
- ✅ Consistent with seed_data.py pattern

### 4. Safe and Verified
- ✅ Tests connection first
- ✅ Verifies all columns after adding
- ✅ Detailed logging and error messages

---

## 🔍 Troubleshooting

### Error: "Questions table does not exist"

**Solution**: Create tables first using seed_data.py:
```bash
python3 src/fastapi_app/seed_data.py
```

### Error: "Permission denied to alter table"

**Solution**: Ensure your database user has ALTER TABLE permissions:
```sql
GRANT ALTER ON TABLE questions TO your_user;
```

### Error: "Module 'fastapi_app' not found"

**Solution**: Make sure you're in the `src` directory:
```bash
cd src
python migrate_add_options.py
```

### Error: "Cannot connect to database"

**Solution**: Check your environment variables:
```bash
# Local
cat .env

# Azure
az webapp config appsettings list --name your-app --resource-group your-rg
```

---

## 📊 Before and After

### Before Migration

Questions table has these columns:
```
id, file_name, subject_name, lesson_title, class_name, 
specialization, question, question_type, question_difficulty, 
page_number, answer_steps, correct_answer, uploaded_by, 
updated_by, created_at, updated_at
```

### After Migration

Questions table includes all the above PLUS:
```
option1, option2, option3, option4, option5, option6
```

**Total columns**: 15 → 21

---

## 🎓 Comparison with seed_data.py

### seed_data.py
```python
from fastapi_app.models import Question, engine, create_db_and_tables

if __name__ == "__main__":
    create_db_and_tables()  # Creates all tables that don't exist
```

### migrate_add_options.py
```python
from fastapi_app.models import Question, engine
from sqlalchemy import inspect, Column, Text
from sqlalchemy.schema import AddColumn

def add_missing_columns(engine):
    # Adds columns to existing table based on Question model
    # Similar approach to seed_data.py but for migrations
```

**Both scripts**:
- ✅ Import from `fastapi_app.models`
- ✅ Use the same `engine` connection
- ✅ Follow SQLAlchemy patterns
- ✅ Are safe to run multiple times

---

## 🔄 Migration Workflow

### Step 1: Initial Setup (Done Once)
```bash
# Create all tables
python3 src/fastapi_app/seed_data.py
```

### Step 2: Add Option Fields (This Migration)
```bash
# Add option columns to questions table
python3 migrate_add_options.py
```

### Step 3: Future Migrations
When you add more fields to models.py in the future, you can create similar migration scripts following this pattern.

---

## 🛡️ Safety Features

### Checks Before Migration
1. ✅ Tests database connection
2. ✅ Verifies questions table exists
3. ✅ Checks which columns already exist

### During Migration
1. ✅ Uses transactions (automatic rollback on error)
2. ✅ Adds columns one at a time
3. ✅ Detailed logging for each step

### After Migration
1. ✅ Verifies all columns were added
2. ✅ Confirms data integrity
3. ✅ Provides summary and next steps

---

## 📚 Related Files

- **models.py** - Question model with option fields defined
- **seed_data.py** - Initial table creation script
- **test_options_feature.py** - Test script for options feature
- **QUICK_START_OPTIONS.md** - Quick start guide for using options

---

## ✅ Post-Migration

After running the migration successfully:

1. **Verify in Database**
   ```sql
   SELECT column_name, data_type, is_nullable
   FROM information_schema.columns
   WHERE table_name = 'questions'
   ORDER BY ordinal_position;
   ```

2. **Test the API**
   ```bash
   python test_options_feature.py
   ```

3. **Extract PDFs**
   ```bash
   # Options will be automatically extracted for Multiple Choice questions
   curl -X POST "http://localhost:8000/extract" \
     -F "file=@textbook.pdf" \
     -F "subject_name=Math" \
     -F "uploaded_by=teacher"
   ```

---

## 🎉 Success!

Once the migration completes successfully, your questions table will support:
- ✨ Up to 6 multiple choice options per question
- ✨ Automatic extraction by LLM
- ✨ Full API support in all endpoints
- ✨ Backward compatibility with existing questions

**You're ready to extract multiple choice questions with options!**

