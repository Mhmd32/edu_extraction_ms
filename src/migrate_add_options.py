"""
Database Migration Script: Add Option Fields to Questions Table

This script adds the option1-option6 fields to the existing questions table.
Run this script if you have an existing database and want to add the new option fields.

Usage:
    python migrate_add_options.py
"""

import logging
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get the database connection URL."""
    sql_url = ""
    
    if os.getenv("WEBSITE_HOSTNAME"):
        logger.info("Connecting to Azure PostgreSQL Flexible server...")
        env_connection_string = os.getenv("AZURE_POSTGRESQL_CONNECTIONSTRING")
        
        if env_connection_string is None:
            raise ValueError("Missing environment variable AZURE_POSTGRESQL_CONNECTIONSTRING")
        
        # Parse the connection string
        details = dict(item.split('=') for item in env_connection_string.split())
        
        # Properly format the URL for SQLAlchemy
        sql_url = (
            f"postgresql://{quote_plus(details['user'])}:{quote_plus(details['password'])}"
            f"@{details['host']}:{details['port']}/{details['dbname']}?sslmode={details['sslmode']}"
        )
    else:
        logger.info("Connecting to local PostgreSQL server...")
        load_dotenv()
        POSTGRES_USERNAME = os.environ.get("DBUSER")
        POSTGRES_PASSWORD = os.environ.get("DBPASS")
        POSTGRES_HOST = os.environ.get("DBHOST")
        POSTGRES_DATABASE = os.environ.get("DBNAME")
        POSTGRES_PORT = os.environ.get("DBPORT", 5432)
        
        if not all([POSTGRES_USERNAME, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_DATABASE]):
            raise ValueError("Missing required database environment variables. Check your .env file.")
        
        sql_url = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"
    
    return sql_url


def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table."""
    query = text("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND column_name = :column_name
        );
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"table_name": table_name, "column_name": column_name})
        return result.scalar()


def add_option_columns(engine):
    """Add option1-option6 columns to the questions table."""
    columns_to_add = [
        "option1",
        "option2",
        "option3",
        "option4",
        "option5",
        "option6"
    ]
    
    logger.info("Starting migration: Adding option columns to questions table...")
    
    columns_added = 0
    columns_skipped = 0
    
    for column_name in columns_to_add:
        try:
            # Check if column already exists
            if check_column_exists(engine, "questions", column_name):
                logger.info(f"  ⏭️  Column '{column_name}' already exists. Skipping.")
                columns_skipped += 1
                continue
            
            # Add the column
            alter_query = text(f"ALTER TABLE questions ADD COLUMN {column_name} TEXT;")
            
            with engine.connect() as conn:
                conn.execute(alter_query)
                conn.commit()
            
            logger.info(f"  ✅ Added column '{column_name}'")
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


def verify_migration(engine):
    """Verify that all option columns were added successfully."""
    logger.info("\nVerifying migration...")
    
    all_columns = ["option1", "option2", "option3", "option4", "option5", "option6"]
    
    for column_name in all_columns:
        exists = check_column_exists(engine, "questions", column_name)
        if exists:
            logger.info(f"  ✅ {column_name}: EXISTS")
        else:
            logger.error(f"  ❌ {column_name}: MISSING")
            return False
    
    logger.info("\n✅ All option columns verified successfully!")
    return True


def main():
    """Main migration function."""
    try:
        logger.info("=" * 60)
        logger.info("Database Migration: Add Option Fields")
        logger.info("=" * 60 + "\n")
        
        # Get database URL
        sql_url = get_database_url()
        logger.info(f"Database URL configured\n")
        
        # Create engine
        engine = create_engine(sql_url)
        
        # Test connection
        logger.info("Testing database connection...")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful!\n")
        
        # Add columns
        add_option_columns(engine)
        
        # Verify
        verify_migration(engine)
        
        logger.info("\n" + "=" * 60)
        logger.info("Migration completed successfully! 🎉")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        logger.error("\nPlease check your database connection and try again.")
        raise


if __name__ == "__main__":
    main()

