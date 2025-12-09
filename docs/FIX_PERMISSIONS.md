# Fix Facebook Token Permissions

## Problem
Your Page Access Token is missing required permissions. The error shows:
```
requires both pages_read_engagement and pages_manage_posts as an admin
```

## Solution: Regenerate Token with Correct Permissions

### Step 1: Go to Graph API Explorer
1. Visit: https://developers.facebook.com/tools/explorer/
2. Select your app from the dropdown (top left)

### Step 2: Generate New Token with Permissions
1. Click **"Generate Access Token"** button
2. In the permissions dialog, make sure to check:
   - ✅ `pages_manage_posts` (required)
   - ✅ `pages_read_engagement` (required)
   - ✅ `pages_show_list` (optional but helpful)
3. Click **"Generate Access Token"**
4. **Authorize** when prompted

### Step 3: Get Long-Lived Page Token
1. In Graph API Explorer, click **"Generate Access Token"** dropdown
2. Select **"Generate Long-Lived Token"**
3. Select your **Page** from the dropdown (not your user account)
4. Copy the long-lived token (starts with `EAAP...`)

### Step 4: Verify Token Permissions
Test the token by running this in Graph API Explorer:
```
GET /me/permissions?access_token={YOUR_PAGE_TOKEN}
```

You should see:
- `pages_manage_posts` with status: `granted`
- `pages_read_engagement` with status: `granted`

### Step 5: Update Your Token
1. **For GitHub Secrets:**
   - Go to your repo → Settings → Secrets → Actions
   - Edit `FB_PAGE_TOKEN` secret
   - Paste your new long-lived token
   - Save

2. **For Local Testing:**
   ```powershell
   $env:FB_PAGE_TOKEN="YOUR_NEW_TOKEN_HERE"
   python newsbot/main.py
   ```

## Alternative: Use Page Token Directly

If the above doesn't work, try getting the token directly from your page:

1. Go to: https://developers.facebook.com/tools/explorer/
2. Select your app
3. In the "User or Page" dropdown, select your **Page** (not your user)
4. Click "Generate Access Token"
5. Grant permissions: `pages_manage_posts`, `pages_read_engagement`
6. Copy the token

## Verify You're Page Admin

Make sure you're an admin of the page:
1. Go to your Facebook Page
2. Settings → Page Roles
3. Verify you're listed as an Admin

---

**After updating the token, test again!**

