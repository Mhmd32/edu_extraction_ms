import logging
import os
import typing
import uuid
from datetime import datetime
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlmodel import Field, SQLModel, create_engine

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

sql_url = ""
if os.getenv("WEBSITE_HOSTNAME"):
    logger.info("Connecting to Azure PostgreSQL Flexible server based on AZURE_POSTGRESQL_CONNECTIONSTRING...")
    env_connection_string = os.getenv("AZURE_POSTGRESQL_CONNECTIONSTRING")
    if env_connection_string is None:
        logger.info("Missing environment variable AZURE_POSTGRESQL_CONNECTIONSTRING")
    else:
        # Parse the connection string
        details = dict(item.split('=') for item in env_connection_string.split())

        # Properly format the URL for SQLAlchemy
        sql_url = (
            f"postgresql://{quote_plus(details['user'])}:{quote_plus(details['password'])}"
            f"@{details['host']}:{details['port']}/{details['dbname']}?sslmode={details['sslmode']}"
        )

else:
    logger.info("Connecting to local PostgreSQL server based on .env file...")
    load_dotenv()
    POSTGRES_USERNAME = os.environ.get("DBUSER")
    POSTGRES_PASSWORD = os.environ.get("DBPASS")
    POSTGRES_HOST = os.environ.get("DBHOST")
    POSTGRES_DATABASE = os.environ.get("DBNAME")
    POSTGRES_PORT = os.environ.get("DBPORT", 5432)

    sql_url = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"

engine = create_engine(sql_url)


def create_db_and_tables():
    return SQLModel.metadata.create_all(engine)

class Restaurant(SQLModel, table=True):
    id: typing.Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)
    street_address: str = Field(max_length=50)
    description: str = Field(max_length=250)

    def __str__(self):
        return f"{self.name}"

class Review(SQLModel, table=True):
    id: typing.Optional[int] = Field(default=None, primary_key=True)
    restaurant: int = Field(foreign_key="restaurant.id")
    user_name: str = Field(max_length=50)
    rating: typing.Optional[int]
    review_text: str = Field(max_length=500)
    review_date: datetime

    def __str__(self):
        return f"{self.name}"


class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: typing.Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(max_length=100, unique=True, index=True)
    display_name: typing.Optional[str] = Field(default=None, max_length=200)
    password_hash: str = Field(max_length=64)
    is_admin: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def __str__(self):
        return f"{self.username}"


class Question(SQLModel, table=True):
    __tablename__ = "questions"
    
    id: typing.Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    file_name: str = Field(max_length=500)
    subject_name: str = Field(max_length=200)
    lesson_title: str = Field(max_length=500)
    class_name: typing.Optional[str] = Field(default=None, max_length=100)
    specialization: typing.Optional[str] = Field(default=None, max_length=200)
    question: str
    question_type: typing.Optional[str] = Field(default=None, max_length=50)
    question_difficulty: typing.Optional[str] = Field(default=None, max_length=20)
    page_number: typing.Optional[str] = Field(default=None, max_length=20)
    answer_steps: typing.Optional[str] = Field(default=None)
    correct_answer: typing.Optional[str] = Field(default=None)
    uploaded_by: str = Field(max_length=100)
    updated_by: typing.Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def __str__(self):
        return f"{self.question[:50]}..."
