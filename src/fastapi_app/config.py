import logging
import os

from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from openai import AsyncOpenAI

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Check if running on Azure
IS_AZURE = os.getenv("WEBSITE_HOSTNAME") is not None

# Load environment variables from .env file only in local development
if not IS_AZURE:
    logger.info("Loading environment variables from .env file (local development)")
    load_dotenv()
else:
    logger.info("Running on Azure - using platform environment variables")

# Azure Document Intelligence Configuration
AZURE_DOC_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT")
AZURE_DOC_INTELLIGENCE_KEY = os.getenv("AZURE_DOC_INTELLIGENCE_KEY")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Default values for database
DEFAULT_UPLOADED_BY = os.getenv("DEFAULT_UPLOADED_BY", "system")
DEFAULT_UPDATED_BY = os.getenv("DEFAULT_UPDATED_BY", None)

# Debug logging (mask sensitive values)
logger.info(f"Environment check - IS_AZURE: {IS_AZURE}")
logger.info(f"AZURE_DOC_INTELLIGENCE_ENDPOINT: {AZURE_DOC_INTELLIGENCE_ENDPOINT[:50] + '...' if AZURE_DOC_INTELLIGENCE_ENDPOINT else 'NOT SET'}")
logger.info(f"AZURE_DOC_INTELLIGENCE_KEY: {'SET (length: ' + str(len(AZURE_DOC_INTELLIGENCE_KEY)) + ')' if AZURE_DOC_INTELLIGENCE_KEY else 'NOT SET'}")
logger.info(f"OPENAI_API_KEY: {'SET (length: ' + str(len(OPENAI_API_KEY)) + ')' if OPENAI_API_KEY else 'NOT SET'}")
logger.info(f"OPENAI_MODEL: {OPENAI_MODEL}")

# Initialize clients
client = None
openai_client = None

# Initialize Azure Document Intelligence client
if AZURE_DOC_INTELLIGENCE_ENDPOINT and AZURE_DOC_INTELLIGENCE_KEY:
    try:
        # Validate endpoint format
        if not AZURE_DOC_INTELLIGENCE_ENDPOINT.startswith(("http://", "https://")):
            logger.error(f"Invalid AZURE_DOC_INTELLIGENCE_ENDPOINT format: {AZURE_DOC_INTELLIGENCE_ENDPOINT}")
            logger.error("Endpoint should start with https://")
        else:
            client = DocumentIntelligenceClient(
                endpoint=AZURE_DOC_INTELLIGENCE_ENDPOINT,
                credential=AzureKeyCredential(AZURE_DOC_INTELLIGENCE_KEY)
            )
            logger.info("✅ Azure Document Intelligence client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Azure Document Intelligence client: {e}")
        logger.error(f"Endpoint: {AZURE_DOC_INTELLIGENCE_ENDPOINT}")
else:
    logger.warning("⚠️ Azure Document Intelligence credentials not found")
    if not AZURE_DOC_INTELLIGENCE_ENDPOINT:
        logger.warning("   - AZURE_DOC_INTELLIGENCE_ENDPOINT is not set")
    if not AZURE_DOC_INTELLIGENCE_KEY:
        logger.warning("   - AZURE_DOC_INTELLIGENCE_KEY is not set")

# Initialize OpenAI client
if OPENAI_API_KEY:
    try:
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenAI client: {e}")
else:
    logger.warning("⚠️ OpenAI API key not found")


# Configuration variables
openai_model = OPENAI_MODEL
default_uploaded_by = DEFAULT_UPLOADED_BY
default_updated_by = DEFAULT_UPDATED_BY

