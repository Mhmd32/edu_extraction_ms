# Azure Web App Troubleshooting Guide

## Error: Azure Document Intelligence client not configured

If you're seeing this error after deployment, follow these steps to diagnose and fix the issue.

## Step 1: Verify Environment Variables in Azure Portal

1. Go to **Azure Portal** → Your Web App
2. Navigate to **Settings** → **Configuration** → **Application settings**
3. Verify these settings exist and have correct values:

| Setting Name | Expected Format | Example |
|--------------|----------------|---------|
| `AZURE_DOC_INTELLIGENCE_ENDPOINT` | `https://your-resource.cognitiveservices.azure.com/` | `https://my-doc-intel.cognitiveservices.azure.com/` |
| `AZURE_DOC_INTELLIGENCE_KEY` | 32-character hex string | `abcd1234...` |
| `OPENAI_API_KEY` | Starts with `sk-` | `sk-proj-...` |
| `OPENAI_MODEL` | Model name (optional) | `gpt-4o` |

### Important Notes:
- ✅ Endpoint MUST end with a `/`
- ✅ Endpoint MUST start with `https://`
- ✅ Key should be 32 characters long
- ✅ No quotes around values in Azure Portal
- ✅ No spaces before or after values

## Step 2: Check Environment Variable Names

Common mistakes:
- ❌ `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` (wrong - has "DOCUMENT")
- ✅ `AZURE_DOC_INTELLIGENCE_ENDPOINT` (correct)
- ❌ `AZURE_DI_KEY` (wrong - custom name)
- ✅ `AZURE_DOC_INTELLIGENCE_KEY` (correct)

## Step 3: Restart the Web App

After adding or changing environment variables, you MUST restart the app:

### Option A: Azure Portal
1. Go to your Web App
2. Click **Restart** at the top
3. Wait 2-3 minutes for the app to fully restart

### Option B: Azure CLI
```bash
az webapp restart \
  --name your-app-name \
  --resource-group your-resource-group
```

## Step 4: Check Application Logs

### View Live Logs
```bash
az webapp log tail \
  --name your-app-name \
  --resource-group your-resource-group
```

Look for these log messages:
- ✅ `Running on Azure - using platform environment variables`
- ✅ `Azure Document Intelligence client initialized successfully`
- ✅ `OpenAI client initialized successfully`

### Download Logs
```bash
az webapp log download \
  --name your-app-name \
  --resource-group your-resource-group \
  --log-file logs.zip
```

## Step 5: Use the Health Check Endpoint

Access the health check endpoint to verify configuration:

```bash
# Replace with your actual URL
curl https://your-app.azurewebsites.net/health
```

Expected response when properly configured:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-20T10:30:00",
  "environment": {
    "is_azure": true,
    "website_hostname": "your-app.azurewebsites.net"
  },
  "services": {
    "database": "connected",
    "azure_document_intelligence": "configured",
    "openai": "configured"
  },
  "configuration": {
    "openai_model": "gpt-4o",
    "default_uploaded_by": "system"
  }
}
```

If you see `"not_configured"` for any service, that service's environment variables are not set correctly.

## Step 6: Verify Azure Document Intelligence Resource

### Check if Resource Exists
```bash
az cognitiveservices account show \
  --name your-doc-intelligence-resource \
  --resource-group your-resource-group
```

### Get the Endpoint
```bash
az cognitiveservices account show \
  --name your-doc-intelligence-resource \
  --resource-group your-resource-group \
  --query properties.endpoint \
  --output tsv
```

### Get the Key
```bash
az cognitiveservices account keys list \
  --name your-doc-intelligence-resource \
  --resource-group your-resource-group \
  --query key1 \
  --output tsv
```

### Verify the Key Works
```bash
# Test the endpoint directly
curl -X POST "https://your-resource.cognitiveservices.azure.com/formrecognizer/documentModels/prebuilt-layout:analyze?api-version=2024-02-29-preview" \
  -H "Ocp-Apim-Subscription-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"urlSource": "https://example.com/sample.pdf"}'
```

## Step 7: Common Configuration Issues

### Issue 1: Environment Variables Not Loading

**Symptoms:**
- Health check shows `"not_configured"`
- Logs show "credentials not found"

**Solution:**
1. Verify variables are in **Application settings**, not **Connection strings**
2. Check for typos in variable names
3. Restart the app after adding variables
4. Wait 2-3 minutes for app to fully reload

### Issue 2: Invalid Endpoint Format

**Symptoms:**
- Logs show "Invalid AZURE_DOC_INTELLIGENCE_ENDPOINT format"

**Solution:**
Ensure endpoint:
- Starts with `https://`
- Ends with `/`
- Example: `https://my-resource.cognitiveservices.azure.com/`

### Issue 3: Wrong API Key

**Symptoms:**
- Client initializes but extraction fails with 401/403 error

**Solution:**
1. Regenerate the key in Azure Portal
2. Update the `AZURE_DOC_INTELLIGENCE_KEY` in Web App settings
3. Restart the app

### Issue 4: Resource in Different Region

**Symptoms:**
- Timeout errors or connection refused

**Solution:**
Ensure Azure Document Intelligence resource and Web App are in the same region or nearby regions.

## Step 8: Enable Detailed Logging

Update Web App logging settings:

```bash
az webapp log config \
  --name your-app-name \
  --resource-group your-resource-group \
  --application-logging filesystem \
  --detailed-error-messages true \
  --failed-request-tracing true \
  --web-server-logging filesystem
```

## Step 9: Check for Deployment Issues

### Verify Deployment Succeeded
```bash
az webapp deployment list-publishing-profiles \
  --name your-app-name \
  --resource-group your-resource-group
```

### Check if Latest Code is Deployed
1. SSH into the Web App:
```bash
az webapp ssh --name your-app-name --resource-group your-resource-group
```

2. Check if config.py exists:
```bash
cd /home/site/wwwroot
ls -la fastapi_app/
cat fastapi_app/config.py
```

3. Verify Python packages are installed:
```bash
pip list | grep azure-ai-documentintelligence
pip list | grep openai
```

## Step 10: Manual Test from SSH Console

If you have SSH access, test the configuration manually:

```bash
# SSH into the app
az webapp ssh --name your-app-name --resource-group your-resource-group

# Run Python interactively
python

# Test configuration
>>> import os
>>> print(os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT"))
>>> print(os.getenv("AZURE_DOC_INTELLIGENCE_KEY"))
>>> print(os.getenv("OPENAI_API_KEY"))
```

If the values are `None`, the environment variables are not set correctly.

## Quick Fix Checklist

- [ ] Environment variables added in Azure Portal (Application settings)
- [ ] Variable names are exactly: `AZURE_DOC_INTELLIGENCE_ENDPOINT`, `AZURE_DOC_INTELLIGENCE_KEY`, `OPENAI_API_KEY`
- [ ] Endpoint ends with `/`
- [ ] Endpoint starts with `https://`
- [ ] No quotes around values
- [ ] No extra spaces
- [ ] Web App restarted after adding variables
- [ ] Waited 2-3 minutes after restart
- [ ] Health check endpoint shows services as "configured"
- [ ] Application logs show successful initialization

## Still Having Issues?

### Check Application Logs for Specific Errors

Look for these patterns in logs:
```
# Good signs:
✅ Running on Azure - using platform environment variables
✅ Azure Document Intelligence client initialized successfully
✅ OpenAI client initialized successfully

# Bad signs:
⚠️ Azure Document Intelligence credentials not found
❌ Failed to initialize Azure Document Intelligence client
```

### Test with cURL

```bash
# Test health endpoint
curl https://your-app.azurewebsites.net/health

# Test extraction endpoint (should fail gracefully with proper error)
curl -X POST "https://your-app.azurewebsites.net/extract" \
  -F "file=@test.pdf" \
  -F "subject_name=test" \
  -F "uploaded_by=test"
```

### Contact Support

If none of the above works, provide:
1. Output from `/health` endpoint
2. Last 50 lines of application logs
3. Screenshot of Application settings in Azure Portal
4. Output from Step 10 (SSH manual test)

## Environment Variable Template

Copy this and fill in your values, then add to Azure Portal:

```
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://YOUR-RESOURCE-NAME.cognitiveservices.azure.com/
AZURE_DOC_INTELLIGENCE_KEY=YOUR_32_CHARACTER_KEY_HERE
OPENAI_API_KEY=sk-YOUR_OPENAI_KEY_HERE
OPENAI_MODEL=gpt-4o
DEFAULT_UPLOADED_BY=system
```

## Verification Commands

After making changes, run these commands to verify:

```bash
# 1. Check health endpoint
curl https://your-app.azurewebsites.net/health | jq

# 2. Stream logs in real-time
az webapp log tail --name your-app-name --resource-group your-resource-group

# 3. Test with a small PDF
curl -X POST "https://your-app.azurewebsites.net/extract" \
  -F "file=@small-test.pdf" \
  -F "subject_name=الرياضيات" \
  -F "uploaded_by=admin"
```

If all checks pass, the configuration is correct and the API should work! 🎉

