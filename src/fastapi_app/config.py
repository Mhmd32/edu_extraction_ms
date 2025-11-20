import logging
import os

from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from openai import AsyncOpenAI

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# Azure Document Intelligence Configuration
AZURE_DOC_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT")
AZURE_DOC_INTELLIGENCE_KEY = os.getenv("AZURE_DOC_INTELLIGENCE_KEY")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Default values for database
DEFAULT_UPLOADED_BY = os.getenv("DEFAULT_UPLOADED_BY", "system")
DEFAULT_UPDATED_BY = os.getenv("DEFAULT_UPDATED_BY", None)

# Initialize clients
client = None
openai_client = None

if AZURE_DOC_INTELLIGENCE_ENDPOINT and AZURE_DOC_INTELLIGENCE_KEY:
    try:
        client = DocumentIntelligenceClient(
            endpoint=AZURE_DOC_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(AZURE_DOC_INTELLIGENCE_KEY)
        )
        logger.info("✅ Azure Document Intelligence client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Azure Document Intelligence client: {e}")
else:
    logger.warning("⚠️ Azure Document Intelligence credentials not found")

if OPENAI_API_KEY:
    try:
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ OpenAI client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
else:
    logger.warning("⚠️ OpenAI API key not found")


# Configuration variables
openai_model = OPENAI_MODEL
default_uploaded_by = DEFAULT_UPLOADED_BY
default_updated_by = DEFAULT_UPDATED_BY

