# Deployment Guide - JSON Parse Error Fix

## 📋 Summary

Fixed the `json.decoder.JSONDecodeError` that was stopping document extraction at page 25 of 150-page documents.

## ✅ Changes Made

### Modified Files
- `src/fastapi_app/app.py` - Enhanced with robust JSON parsing and error handling

### New Files
- `src/JSON_PARSE_ERROR_FIX.md` - Detailed technical documentation
- `src/QUICK_FIX_SUMMARY.md` - Quick reference guide
- `src/FIX_DEPLOYMENT_GUIDE.md` - This file

## 🚀 Deployment Steps

### 1. Test Locally (Optional but Recommended)

```bash
# Navigate to project directory
cd c:\Users\HP\Documents\GitHub\edu_extraction_ms

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run the application
cd src
uvicorn fastapi_app.app:app --reload
```

Test with your problematic 150-page document:
```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@your-150-page-document.pdf" \
  -F "subject_name=الرياضيات" \
  -F "class_name=الصف الثاني عشر" \
  -F "uploaded_by=teacher1"
```

### 2. Commit Changes

```bash
# Stage the changes
git add src/fastapi_app/app.py
git add src/JSON_PARSE_ERROR_FIX.md
git add src/QUICK_FIX_SUMMARY.md
git add src/FIX_DEPLOYMENT_GUIDE.md

# Commit with descriptive message
git commit -m "Fix: Robust JSON parsing for document extraction

- Add OpenAI json_object response format
- Implement retry logic with exponential backoff
- Add multi-strategy JSON parsing and repair
- Enable graceful degradation for failed pages
- Enhance error logging and tracking
- Add pages_failed metric to response

Fixes JSON parse errors at page 25 and allows extraction to continue on failures."

# Push to repository
git push origin prod
```

### 3. Deploy to Azure

The deployment will happen automatically via GitHub Actions when you push to the `prod` branch.

**Monitor deployment:**
- Check GitHub Actions at: https://github.com/YOUR_USERNAME/edu_extraction_ms/actions
- Wait for the deployment workflow to complete (usually 3-5 minutes)

### 4. Verify Deployment

Once deployed, test the health endpoint:
```bash
curl https://your-azure-app.azurewebsites.net/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "azure_document_intelligence": "configured",
    "openai": "configured"
  }
}
```

### 5. Re-run Failed Extraction

Now re-run the extraction on your 150-page document:

```bash
curl -X POST "https://your-azure-app.azurewebsites.net/extract" \
  -F "file=@your-150-page-document.pdf" \
  -F "subject_name=الرياضيات" \
  -F "class_name=الصف الثاني عشر" \
  -F "uploaded_by=teacher1"
```

Expected behavior:
- ✅ All pages will be processed
- ⚠️ Page 25 may show "no_questions_found" if issues persist
- ✅ Pages 26-150 will continue processing
- 📊 Response will show summary with `pages_failed` count

## 📊 What to Monitor

### Successful Response
```json
{
  "status": "success",
  "message": "Processed 150 page(s); stored 487 question(s).",
  "summary": {
    "total_pages_detected": 150,
    "pages_with_content": 150,
    "pages_skipped": 0,
    "pages_failed": 0,
    "questions_stored": 487
  }
}
```

### Partial Success Response (some pages failed)
```json
{
  "status": "partial_success",
  "message": "Processed 150 page(s) with 1 failure(s); stored 487 question(s).",
  "summary": {
    "total_pages_detected": 150,
    "pages_with_content": 150,
    "pages_skipped": 0,
    "pages_failed": 1,
    "questions_stored": 487,
    "pages": [
      {
        "page_number": 25,
        "questions_extracted": 0,
        "status": "no_questions_found"
      }
    ]
  }
}
```

## 🔍 Azure Logs

To check logs in Azure:

1. Go to Azure Portal
2. Navigate to your App Service
3. Click "Log stream" or "Logs"
4. Look for these messages:

**Success:**
```
✅ Successfully extracted 12 questions
```

**Retry:**
```
⚠️ JSON parse failed on attempt 1, retrying in 1s...
OpenAI extraction attempt 2/3 for page 25
```

**Graceful failure:**
```
⚠️ Returning empty list for page 25 due to persistent JSON errors
```

## 🔧 Rollback (If Needed)

If issues arise, rollback to previous version:

```bash
# Rollback the commit
git revert HEAD

# Push the revert
git push origin prod
```

However, this fix is **strongly recommended** as it makes the system significantly more robust.

## 📝 No Configuration Changes

- ✅ No environment variables to update
- ✅ No database migrations needed
- ✅ No API contract changes
- ✅ 100% backward compatible

## ✅ Testing Checklist

- [ ] Code committed to git
- [ ] Pushed to `prod` branch
- [ ] GitHub Actions deployment successful
- [ ] Health check endpoint responds
- [ ] Re-run extraction on 150-page document
- [ ] Verify all pages processed
- [ ] Check logs for retry messages
- [ ] Verify questions stored in database
- [ ] Check `pages_failed` metric in response

## 🎯 Success Criteria

✅ **Fix is successful if:**
1. Extraction completes for all 150 pages (doesn't stop at page 25)
2. Questions are extracted from pages 1-24 and 26-150
3. Response includes `pages_failed` count
4. Logs show retry attempts if JSON parsing fails
5. System continues processing after failures

## 📞 Support

If issues persist after deployment:

1. Check Azure logs for specific error messages
2. Verify OpenAI API key is valid and has quota
3. Check Azure Document Intelligence service is running
4. Verify database connection is healthy
5. Review the detailed logs around page 25 for specific errors

## 🔗 Related Documentation

- `JSON_PARSE_ERROR_FIX.md` - Detailed technical explanation
- `QUICK_FIX_SUMMARY.md` - Quick reference guide
- Azure deployment workflows: `.github/workflows/prod_eduextract.yml`

---

**Status**: ✅ Ready for deployment
**Priority**: High
**Breaking Changes**: None
**Estimated Deployment Time**: 5 minutes
