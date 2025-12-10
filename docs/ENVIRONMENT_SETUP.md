# Environment Variables Setup Guide

This guide explains how to set up environment variables for the Swedish News Bot, both locally and in GitHub Actions.

## Required Environment Variables

- `FB_PAGE_ID` - Your Facebook Page ID
- `FB_PAGE_TOKEN` - Your long-lived Facebook Page Access Token
- `OPENAI_API_KEY` - Your OpenAI API key (for article generation)

## Local Setup (Windows)

### Option 1: PowerShell Session (Temporary)

Set variables for the current PowerShell session:

```powershell
$env:FB_PAGE_ID="880794241790973"
$env:FB_PAGE_TOKEN="your_token_here"
$env:OPENAI_API_KEY="your_openai_key_here"
```

**Note:** These variables are lost when you close the terminal.

### Option 2: User Environment Variables (Permanent)

Set system-wide user environment variables:

1. **Open System Properties:**
   - Press `Win + R`
   - Type `sysdm.cpl` and press Enter
   - Click "Environment Variables"

2. **Add User Variables:**
   - Under "User variables", click "New"
   - Add each variable:
     - Variable name: `FB_PAGE_ID`
     - Variable value: `880794241790973`
   - Repeat for `FB_PAGE_TOKEN` and `OPENAI_API_KEY`

3. **Restart your terminal/PowerShell** for changes to take effect

### Option 3: PowerShell Profile (Recommended for Development)

Add to your PowerShell profile for automatic loading:

1. **Open your PowerShell profile:**
   ```powershell
   notepad $PROFILE
   ```

2. **Add these lines:**
   ```powershell
   $env:FB_PAGE_ID="880794241790973"
   $env:FB_PAGE_TOKEN="your_token_here"
   $env:OPENAI_API_KEY="your_openai_key_here"
   ```

3. **Save and reload:**
   ```powershell
   . $PROFILE
   ```

### Option 4: .env File (Using python-dotenv)

1. **Install python-dotenv:**
   ```powershell
   pip install python-dotenv
   ```

2. **Create `.env` file** in the project root:
   ```
   FB_PAGE_ID=880794241790973
   FB_PAGE_TOKEN=your_token_here
   OPENAI_API_KEY=your_openai_key_here
   ```

3. **Update `main.py`** to load from .env:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

## Local Setup (Linux/Mac)

### Option 1: Shell Session (Temporary)

```bash
export FB_PAGE_ID="880794241790973"
export FB_PAGE_TOKEN="your_token_here"
export OPENAI_API_KEY="your_openai_key_here"
```

### Option 2: Shell Profile (Permanent)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export FB_PAGE_ID="880794241790973"
export FB_PAGE_TOKEN="your_token_here"
export OPENAI_API_KEY="your_openai_key_here"
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Option 3: .env File

Same as Windows Option 4 above.

## GitHub Actions Setup

### Step 1: Go to Repository Settings

1. Navigate to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**

### Step 2: Add Repository Secrets

Click **"New repository secret"** and add each secret:

1. **Name:** `FB_PAGE_ID`
   - **Value:** `880794241790973`

2. **Name:** `FB_PAGE_TOKEN`
   - **Value:** Your long-lived page access token

3. **Name:** `OPENAI_API_KEY`
   - **Value:** Your OpenAI API key

### Step 3: Verify Workflow File

The workflow file (`.github/workflows/daily-post.yml`) should reference these secrets:

```yaml
env:
  FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
  FB_PAGE_TOKEN: ${{ secrets.FB_PAGE_TOKEN }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Current Configuration

**Page ID:** `880794241790973`

**Token:** (Set in your environment variables or GitHub Secrets)

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `.env` files or tokens to git
- `.env` is already in `.gitignore`
- GitHub Secrets are encrypted and only accessible to workflows
- Tokens should be kept private and secure

## Verifying Setup

### Local Verification

Run the bot locally:
```powershell
python newsbot/main.py
```

The bot will validate the Facebook token at startup and show clear error messages if something is wrong.

### GitHub Actions Verification

1. Go to **Actions** tab in GitHub
2. Click **"Daily News Post to Facebook"**
3. Click **"Run workflow"** → **"Run workflow"**
4. Check the logs to verify the bot runs successfully

## Troubleshooting

### "Facebook credentials not set"
- Verify environment variables are set: `echo $env:FB_PAGE_ID` (PowerShell) or `echo $FB_PAGE_ID` (Linux/Mac)
- Restart your terminal after setting system environment variables

### "Token validation failed"
- Check token is valid at: https://developers.facebook.com/tools/debug/accesstoken/
- Verify token has required permissions: `pages_read_engagement`, `pages_manage_posts`
- Ensure token is a Page Access Token, not a User Access Token

### "GitHub Actions failing"
- Verify all secrets are set in repository settings
- Check secret names match exactly (case-sensitive)
- Review workflow logs for specific error messages

