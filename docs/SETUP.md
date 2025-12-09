# Quick Setup Guide

## Your Facebook Credentials

✅ **Page ID:** `880794241790973`  
✅ **Long-lived Page Access Token:** (Provided - keep it secure!)

## Step 1: Set GitHub Secrets

1. Go to your GitHub repository
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"** and add:

   **Secret 1:**
   - Name: `FB_PAGE_ID`
   - Value: `880794241790973`

   **Secret 2:**
   - Name: `FB_PAGE_TOKEN`
   - Value: `EAAPQ4FidXrQBQGffHZAwvFtma8u1CPiRtiCKGkcPvIbfyZAlhz3qzOvJT85ZBddb6WFNcjuF7wrY0fcyHHJ9IMt7DQ3NkaabznGhlUEfVd9XZCZBPwL8UKgjHrXSBXcyxZB74AQ6qZAmqgZBTZArJ5EITWbbQZC1VpZBLt6Gl09bZCBFB94eGpVJxBReSdWd3N0opZBgtHWZAPZBGKzJIQ3PwZDZD`

## Step 2: Test Locally (Optional)

### Windows PowerShell:
```powershell
$env:FB_PAGE_ID="880794241790973"
$env:FB_PAGE_TOKEN="EAAPQ4FidXrQBQGffHZAwvFtma8u1CPiRtiCKGkcPvIbfyZAlhz3qzOvJT85ZBddb6WFNcjuF7wrY0fcyHHJ9IMt7DQ3NkaabznGhlUEfVd9XZCZBPwL8UKgjHrXSBXcyxZB74AQ6qZAmqgZBTZArJ5EITWbbQZC1VpZBLt6Gl09bZCBFB94eGpVJxBReSdWd3N0opZBgtHWZAPZBGKzJIQ3PwZDZD"
python newsbot/main.py
```

### Linux/Mac:
```bash
export FB_PAGE_ID="880794241790973"
export FB_PAGE_TOKEN="EAAPQ4FidXrQBQGffHZAwvFtma8u1CPiRtiCKGkcPvIbfyZAlhz3qzOvJT85ZBddb6WFNcjuF7wrY0fcyHHJ9IMt7DQ3NkaabznGhlUEfVd9XZCZBPwL8UKgjHrXSBXcyxZB74AQ6qZAmqgZBTZArJ5EITWbbQZC1VpZBLt6Gl09bZCBFB94eGpVJxBReSdWd3N0opZBgtHWZAPZBGKzJIQ3PwZDZD"
python newsbot/main.py
```

## Step 3: Push to GitHub

Once you've set the secrets, push your code to GitHub:

```bash
git add .
git commit -m "Initial commit: Swedish news bot"
git push
```

## Step 4: Test GitHub Actions

1. Go to the **Actions** tab in your GitHub repository
2. Select **"Daily News Post to Facebook"** workflow
3. Click **"Run workflow"** → **"Run workflow"** (manual trigger)
4. Watch it run and check the logs

## ⚠️ Security Notes

- **NEVER** commit your access token to git
- The `.gitignore` file protects `posted.json` and `.env` files
- Tokens expire after ~60 days - you'll need to regenerate
- If your token is exposed, revoke it immediately in Facebook Developer settings

## Next Steps

- The bot will run automatically at **08:00 Sweden time** daily
- You can manually trigger it anytime from the Actions tab
- Check `newsbot/posted.json` to see which articles have been posted
- Monitor the Actions logs for any errors

---

**Ready to go! 🚀**

