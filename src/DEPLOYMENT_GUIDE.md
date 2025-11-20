# Deployment Guide for Question Extraction API

## Overview

This guide will help you deploy the Question Extraction API to Azure Web App with all the required services.

## Prerequisites

1. Azure Account
2. Azure CLI installed
3. Python 3.10+
4. Git

## Azure Services Required

1. **Azure Web App** (for hosting the FastAPI application)
2. **Azure Database for PostgreSQL** (for storing questions and users)
3. **Azure Document Intelligence** (for PDF text extraction)
4. **OpenAI API Key** (for question extraction with GPT-4)

## Setup Steps

### 1. Create Azure Document Intelligence Resource

```bash
# Create resource group (if not exists)
az group create --name my-resource-group --location eastus

# Create Document Intelligence resource
az cognitiveservices account create \
  --name my-doc-intelligence \
  --resource-group my-resource-group \
  --kind FormRecognizer \
  --sku S0 \
  --location eastus \
  --yes

# Get the endpoint and key
az cognitiveservices account show \
  --name my-doc-intelligence \
  --resource-group my-resource-group \
  --query properties.endpoint \
  --output tsv

az cognitiveservices account keys list \
  --name my-doc-intelligence \
  --resource-group my-resource-group \
  --query key1 \
  --output tsv
```

### 2. Create Azure PostgreSQL Database

```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --name my-postgres-server \
  --resource-group my-resource-group \
  --location eastus \
  --admin-user myadmin \
  --admin-password 'YourSecurePassword123!' \
  --sku-name Standard_B2s \
  --tier Burstable \
  --version 14 \
  --storage-size 32

# Create database
az postgres flexible-server db create \
  --resource-group my-resource-group \
  --server-name my-postgres-server \
  --database-name questions_db

# Allow Azure services
az postgres flexible-server firewall-rule create \
  --resource-group my-resource-group \
  --name my-postgres-server \
  --rule-name AllowAllAzureIPs \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Get connection string
az postgres flexible-server show-connection-string \
  --server-name my-postgres-server \
  --database-name questions_db \
  --admin-user myadmin \
  --admin-password 'YourSecurePassword123!'
```

### 3. Create Azure Web App

```bash
# Create App Service Plan
az appservice plan create \
  --name my-app-plan \
  --resource-group my-resource-group \
  --location eastus \
  --sku B2 \
  --is-linux

# Create Web App
az webapp create \
  --name my-question-extraction-app \
  --resource-group my-resource-group \
  --plan my-app-plan \
  --runtime "PYTHON:3.11"
```

### 4. Configure Environment Variables

Add these application settings to your Azure Web App:

```bash
# Database connection (formatted for Azure)
az webapp config appsettings set \
  --name my-question-extraction-app \
  --resource-group my-resource-group \
  --settings \
    AZURE_POSTGRESQL_CONNECTIONSTRING="host=my-postgres-server.postgres.database.azure.com port=5432 dbname=questions_db user=myadmin password=YourSecurePassword123! sslmode=require" \
    AZURE_DOC_INTELLIGENCE_ENDPOINT="https://my-doc-intelligence.cognitiveservices.azure.com/" \
    AZURE_DOC_INTELLIGENCE_KEY="your_document_intelligence_key" \
    OPENAI_API_KEY="your_openai_api_key" \
    OPENAI_MODEL="gpt-4o" \
    DEFAULT_UPLOADED_BY="system" \
    RUNNING_IN_PRODUCTION="true"
```

Or use the Azure Portal:
1. Go to your Web App
2. Navigate to **Configuration** > **Application Settings**
3. Add the following settings:

| Name | Value |
|------|-------|
| `AZURE_POSTGRESQL_CONNECTIONSTRING` | `host=... port=5432 dbname=... user=... password=... sslmode=require` |
| `AZURE_DOC_INTELLIGENCE_ENDPOINT` | `https://your-resource.cognitiveservices.azure.com/` |
| `AZURE_DOC_INTELLIGENCE_KEY` | `your_key_here` |
| `OPENAI_API_KEY` | `sk-...` |
| `OPENAI_MODEL` | `gpt-4o` |
| `DEFAULT_UPLOADED_BY` | `system` |
| `RUNNING_IN_PRODUCTION` | `true` |

### 5. Deploy the Application

#### Option A: Deploy from Local Git

```bash
# Configure deployment user (one-time setup)
az webapp deployment user set \
  --user-name your-deployment-username \
  --password your-deployment-password

# Configure local git
az webapp deployment source config-local-git \
  --name my-question-extraction-app \
  --resource-group my-resource-group

# Add Azure remote and push
git remote add azure <deployment-git-url>
git push azure main:master
```

#### Option B: Deploy from GitHub

```bash
az webapp deployment source config \
  --name my-question-extraction-app \
  --resource-group my-resource-group \
  --repo-url https://github.com/your-username/your-repo \
  --branch main \
  --manual-integration
```

#### Option C: Deploy via ZIP

```bash
# Package the application
cd src
zip -r ../app.zip .

# Deploy
az webapp deployment source config-zip \
  --name my-question-extraction-app \
  --resource-group my-resource-group \
  --src ../app.zip
```

### 6. Initialize the Database

After deployment, run the seed script to create tables:

```bash
# SSH into the Web App
az webapp ssh --name my-question-extraction-app --resource-group my-resource-group

# Inside the SSH session
python -m fastapi_app.seed_data
```

Or create a startup script in `startup.sh`:

```bash
#!/bin/bash
python -m fastapi_app.seed_data
gunicorn -c gunicorn.conf.py fastapi_app.app:app
```

### 7. Test the Deployment

```bash
# Get the app URL
az webapp show \
  --name my-question-extraction-app \
  --resource-group my-resource-group \
  --query defaultHostName \
  --output tsv

# Test the API
curl https://your-app.azurewebsites.net/
```

## Local Development Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd edu_extraction_ms/src
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Create `.env` file:
```env
DBUSER=postgres
DBPASS=yourpassword
DBHOST=localhost
DBNAME=questions_db
DBPORT=5432

AZURE_DOC_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOC_INTELLIGENCE_KEY=your_key

OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o

DEFAULT_UPLOADED_BY=system
```

5. Initialize database:
```bash
python -m fastapi_app.seed_data
```

6. Run the application:
```bash
uvicorn fastapi_app.app:app --reload
```

7. Access the API:
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Testing the API

### Create a User

```bash
curl -X POST "https://your-app.azurewebsites.net/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "display_name": "Administrator",
    "is_admin": true
  }'
```

### Extract Questions from PDF

```bash
curl -X POST "https://your-app.azurewebsites.net/extract" \
  -F "file=@textbook.pdf" \
  -F "subject_name=الرياضيات" \
  -F "class_name=الصف الثاني عشر" \
  -F "uploaded_by=admin"
```

### List Questions

```bash
curl "https://your-app.azurewebsites.net/questions?subject_name=الرياضيات&limit=10"
```

## Monitoring and Troubleshooting

### View Application Logs

```bash
# Stream logs
az webapp log tail \
  --name my-question-extraction-app \
  --resource-group my-resource-group

# Download logs
az webapp log download \
  --name my-question-extraction-app \
  --resource-group my-resource-group \
  --log-file logs.zip
```

### Enable Application Insights (Optional)

```bash
# Create Application Insights
az monitor app-insights component create \
  --app my-app-insights \
  --location eastus \
  --resource-group my-resource-group

# Get connection string
az monitor app-insights component show \
  --app my-app-insights \
  --resource-group my-resource-group \
  --query connectionString \
  --output tsv

# Add to Web App settings
az webapp config appsettings set \
  --name my-question-extraction-app \
  --resource-group my-resource-group \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="your-connection-string"
```

## Security Best Practices

1. **Use Managed Identity** for Azure services (instead of keys)
2. **Enable HTTPS only** on the Web App
3. **Implement authentication** for API endpoints
4. **Use Azure Key Vault** for secrets
5. **Enable CORS** only for trusted domains
6. **Set up rate limiting** to prevent abuse
7. **Regularly update dependencies**

## Cost Optimization

1. Use **Burstable tier** for PostgreSQL in development
2. Use **B1/B2 App Service Plan** for testing
3. Consider **consumption-based pricing** for Document Intelligence
4. Monitor **OpenAI API usage** and set budget alerts
5. Use **Auto-scaling** for production workloads

## Support

For issues or questions, please contact the development team or create an issue in the repository.

