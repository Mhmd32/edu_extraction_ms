# Quick Fix: Azure Environment Variables Configuration

## Problem
Error: `Azure Document Intelligence client not configured`

## Solution (5 minutes)

### Step 1: Set Environment Variables via Azure CLI

Replace `YOUR-APP-NAME` and `YOUR-RESOURCE-GROUP` with your actual values:

```bash
# Set your app details
APP_NAME="YOUR-APP-NAME"
RESOURCE_GROUP="YOUR-RESOURCE-GROUP"
DOC_INTEL_NAME="YOUR-DOC-INTELLIGENCE-RESOURCE-NAME"

# Get the Document Intelligence endpoint and key
ENDPOINT=$(az cognitiveservices account show \
  --name $DOC_INTEL_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.endpoint \
  --output tsv)

KEY=$(az cognitiveservices account keys list \
  --name $DOC_INTEL_NAME \
  --resource-group $RESOURCE_GROUP \
  --query key1 \
  --output tsv)

# Set all environment variables at once
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AZURE_DOC_INTELLIGENCE_ENDPOINT="$ENDPOINT" \
    AZURE_DOC_INTELLIGENCE_KEY="$KEY" \
    OPENAI_API_KEY="YOUR_OPENAI_KEY_HERE" \
    OPENAI_MODEL="gpt-4o" \
    DEFAULT_UPLOADED_BY="system"
```

### Step 2: Restart the App

```bash
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP
```

### Step 3: Wait 2 Minutes

Wait for the app to fully restart (this is important!)

### Step 4: Verify Configuration

```bash
# Check health endpoint
curl https://$APP_NAME.azurewebsites.net/health | python -m json.tool
```

**Expected Output:**
```json
{
  "status": "healthy",
  "services": {
    "azure_document_intelligence": "configured",
    "openai": "configured",
    "database": "connected"
  }
}
```

### Step 5: Check Logs

```bash
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP
```

**Look for these messages:**
```
✅ Running on Azure - using platform environment variables
✅ Azure Document Intelligence client initialized successfully
✅ OpenAI client initialized successfully
```

---

## Alternative: Set via Azure Portal (GUI Method)

### Step 1: Get Your Keys

**Document Intelligence:**
1. Go to Azure Portal
2. Search for your Document Intelligence resource
3. Go to **Keys and Endpoint**
4. Copy **Endpoint** and **KEY 1**

**OpenAI:**
1. Go to https://platform.openai.com/api-keys
2. Create or copy your API key (starts with `sk-`)

### Step 2: Add to Web App

1. Go to your **Web App** in Azure Portal
2. Click **Configuration** (left menu)
3. Click **Application settings** tab
4. Click **+ New application setting** for each:

| Name | Value | Example |
|------|-------|---------|
| `AZURE_DOC_INTELLIGENCE_ENDPOINT` | Your endpoint with trailing `/` | `https://myresource.cognitiveservices.azure.com/` |
| `AZURE_DOC_INTELLIGENCE_KEY` | Your 32-char key | `abc123...` |
| `OPENAI_API_KEY` | Your OpenAI key | `sk-proj-...` |
| `OPENAI_MODEL` | `gpt-4o` | `gpt-4o` |
| `DEFAULT_UPLOADED_BY` | `system` | `system` |

5. Click **Save** at the top
6. Click **Continue** to confirm restart

### Step 3: Wait 2-3 Minutes

The app needs time to restart and load the new variables.

### Step 4: Test

Go to: `https://your-app-name.azurewebsites.net/health`

You should see:
```json
{
  "status": "healthy",
  "services": {
    "azure_document_intelligence": "configured",
    "openai": "configured"
  }
}
```

---

## Common Mistakes to Avoid

### ❌ Wrong Variable Names
```
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT  ❌ (has "DOCUMENT")
AZURE_DI_ENDPOINT                     ❌ (wrong abbreviation)
```

### ✅ Correct Variable Names
```
AZURE_DOC_INTELLIGENCE_ENDPOINT       ✅
AZURE_DOC_INTELLIGENCE_KEY            ✅
OPENAI_API_KEY                        ✅
```

### ❌ Wrong Endpoint Format
```
https://resource.cognitiveservices.azure.com    ❌ (missing trailing /)
http://resource.cognitiveservices.azure.com/    ❌ (http instead of https)
resource.cognitiveservices.azure.com/           ❌ (missing https://)
```

### ✅ Correct Endpoint Format
```
https://resource.cognitiveservices.azure.com/   ✅
```

### ❌ Adding Quotes in Azure Portal
```
Value: "https://resource.cognitiveservices.azure.com/"   ❌ (has quotes)
Value: 'sk-abc123...'                                    ❌ (has quotes)
```

### ✅ No Quotes in Azure Portal
```
Value: https://resource.cognitiveservices.azure.com/     ✅
Value: sk-abc123...                                      ✅
```

---

## Verification Checklist

After completing the steps above, verify:

- [ ] Health endpoint returns `"status": "healthy"`
- [ ] All services show `"configured"` in health check
- [ ] Application logs show "✅ initialized successfully" messages
- [ ] No "⚠️" warning messages in logs about missing credentials
- [ ] Endpoint ends with `/`
- [ ] Endpoint starts with `https://`
- [ ] Keys have no quotes or spaces
- [ ] App was restarted after setting variables
- [ ] Waited at least 2 minutes after restart

---

## Still Not Working?

### Check What the App Sees

```bash
# SSH into your app
az webapp ssh --name $APP_NAME --resource-group $RESOURCE_GROUP

# Check environment variables
env | grep AZURE_DOC_INTELLIGENCE
env | grep OPENAI

# Test Python import
python -c "import os; print('Endpoint:', os.getenv('AZURE_DOC_INTELLIGENCE_ENDPOINT')); print('Key length:', len(os.getenv('AZURE_DOC_INTELLIGENCE_KEY', '')))"
```

If the values are empty or `None`, the environment variables are not set correctly in Azure.

### Force Redeploy

Sometimes a redeploy helps:

```bash
# Redeploy the app
az webapp deployment source config-zip \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --src app.zip
```

### Check App Service Plan

Ensure your App Service Plan has enough resources:
- Minimum: B1 (Basic) tier
- Recommended: B2 or higher for production

---

## Success Indicators

When everything is working correctly:

**Health Endpoint:**
```json
{
  "status": "healthy",
  "environment": {
    "is_azure": true
  },
  "services": {
    "database": "connected",
    "azure_document_intelligence": "configured",
    "openai": "configured"
  }
}
```

**Application Logs:**
```
Running on Azure - using platform environment variables
Environment check - IS_AZURE: True
AZURE_DOC_INTELLIGENCE_ENDPOINT: https://...
AZURE_DOC_INTELLIGENCE_KEY: SET (length: 32)
OPENAI_API_KEY: SET (length: 51)
✅ Azure Document Intelligence client initialized successfully
✅ OpenAI client initialized successfully
```

**Test Extraction Works:**
```bash
curl -X POST "https://your-app.azurewebsites.net/extract" \
  -F "file=@test.pdf" \
  -F "subject_name=الرياضيات" \
  -F "uploaded_by=admin"

# Should return JSON with extraction results, not an error
```

---

## Need Help?

1. Run `/health` endpoint and copy the output
2. Run log tail command and copy the last 20 lines
3. Screenshot your Azure Portal Application Settings
4. Check the AZURE_TROUBLESHOOTING.md file for detailed diagnostics

Good luck! 🚀

