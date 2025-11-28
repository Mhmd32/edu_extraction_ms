"""
Database Migration Script: Add Option Fields to Questions Table

This script adds the option1-option6 fields to the existing questions table.
It uses SQLAlchemy to inspect the database and add missing columns based on the models.py definition.

Similar to how seed_data.py creates tables, this script adds columns to existing tables.

Usage:
    python migrate_add_options.py
    
    Or on Azure:
    python3 migrate_add_options.py
"""

import logging
from sqlalchemy import Column, Text, inspect
from sqlalchemy.schema import AddColumn

from fastapi_app.models import Question, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_existing_columns(engine, table_name):
    """Get list of existing columns in a table."""
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return {col['name'] for col in columns}


def add_missing_columns(engine):
    """Add missing option columns to the questions table based on the Question model."""
    
    # Option columns we want to add
    option_columns = {
        'option1': Text,
        'option2': Text,
        'option3': Text,
        'option4': Text,
        'option5': Text,
        'option6': Text,
    }
    
    logger.info("Starting migration: Adding option columns to questions table...")
    logger.info("Reading schema from Question model in models.py\n")
    
    # Get existing columns from database
    try:
        existing_columns = get_existing_columns(engine, 'questions')
        logger.info(f"Found {len(existing_columns)} existing columns in questions table")
    except Exception as e:
        logger.error(f"Failed to inspect questions table: {e}")
        raise
    
    columns_added = 0
    columns_skipped = 0
    
    # Add missing columns
    for column_name, column_type in option_columns.items():
        if column_name in existing_columns:
            logger.info(f"  ⏭️  Column '{column_name}' already exists. Skipping.")
            columns_skipped += 1
            continue
        
        try:
            # Create column definition
            column = Column(column_name, column_type, nullable=True)
            
            # Add column to table
            with engine.begin() as conn:
                conn.execute(AddColumn('questions', column))
            
            logger.info(f"  ✅ Added column '{column_name}' (TEXT, nullable)")
            columns_added += 1
            
        except Exception as e:
            logger.error(f"  ❌ Failed to add column '{column_name}': {e}")
            raise
    
    logger.info("\n" + "=" * 60)
    logger.info("Migration completed!")
    logger.info(f"  Columns added: {columns_added}")
    logger.info(f"  Columns skipped (already exist): {columns_skipped}")
    logger.info("=" * 60)
    
    if columns_added > 0:
        logger.info("\n✨ Your database has been successfully updated!")
        logger.info("The questions table now supports multiple choice options.")
    else:
        logger.info("\n✨ All columns already exist. No changes needed.")
    
    return columns_added, columns_skipped


def verify_migration(engine):
    """Verify that all option columns exist in the database."""
    logger.info("\nVerifying migration...")
    
    required_columns = ['option1', 'option2', 'option3', 'option4', 'option5', 'option6']
    existing_columns = get_existing_columns(engine, 'questions')
    
    all_present = True
    for column_name in required_columns:
        if column_name in existing_columns:
            logger.info(f"  ✅ {column_name}: EXISTS")
        else:
            logger.error(f"  ❌ {column_name}: MISSING")
            all_present = False
    
    if all_present:
        logger.info("\n✅ All option columns verified successfully!")
    else:
        logger.error("\n❌ Some columns are missing!")
    
    return all_present


def main():
    """Main migration function."""
    try:
        logger.info("=" * 60)
        logger.info("Database Migration: Add Option Fields")
        logger.info("Using SQLAlchemy schema from models.py")
        logger.info("=" * 60 + "\n")
        
        # Test connection
        logger.info("Testing database connection...")
        with engine.connect():
            pass
        logger.info("✅ Database connection successful!\n")
        
        # Add missing columns
        columns_added, columns_skipped = add_missing_columns(engine)
        
        # Verify
        verify_migration(engine)
        
        logger.info("\n" + "=" * 60)
        logger.info("Migration completed successfully! 🎉")
        logger.info("=" * 60)
        
        logger.info("\n📝 Summary:")
        logger.info(f"  - New columns added: {columns_added}")
        logger.info(f"  - Existing columns skipped: {columns_skipped}")
        logger.info(f"  - Total option fields: 6")
        
        if columns_added > 0:
            logger.info("\n🎓 Next steps:")
            logger.info("  1. Extract PDFs with multiple choice questions")
            logger.info("  2. Options will be automatically extracted by the LLM")
            logger.info("  3. Test with: python test_options_feature.py")
        
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        logger.error("\nPlease check:")
        logger.error("  1. Database connection is configured (.env file)")
        logger.error("  2. Questions table exists in the database")
        logger.error("  3. You have permission to alter tables")
        raise


if __name__ == "__main__":
    main()

