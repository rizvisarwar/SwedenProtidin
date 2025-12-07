# Swedish News to Facebook Bot 🇸🇪→🇧🇩

An automated system that fetches Swedish news headlines from RSS feeds, translates them to Bangla, adds summaries, and posts to a Facebook Page. Runs daily via GitHub Actions at 08:00 Sweden time.

## Features

- ✅ Fetches news from multiple Swedish RSS feeds
- ✅ Translates headlines and summaries to Bangla using free googletrans library
- ✅ Creates 3-bullet point summaries
- ✅ Auto-posts to Facebook Page
- ✅ Tracks posted articles to avoid duplicates
- ✅ Runs daily via GitHub Actions (zero cost)
- ✅ Comprehensive logging

## Project Structure

```
.
├── newsbot/
│   ├── main.py           # Main bot script
│   ├── rss_list.json     # RSS feed URLs
│   └── posted.json       # Posted articles database (auto-generated)
├── .github/
│   └── workflows/
│       └── post.yml      # GitHub Actions workflow
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Setup Instructions

### 1. Facebook Developer App Setup

1. **Create a Facebook App:**
   - Go to [Facebook Developers](https://developers.facebook.com/)
   - Click "My Apps" → "Create App"
   - Choose "Business" as the app type
   - Fill in app name and contact email
   - Click "Create App"

2. **Add Facebook Login Product:**
   - In your app dashboard, click "Add Product"
   - Find "Facebook Login" and click "Set Up"
   - Use default settings and click "Save"

3. **Get Page Access Token:**
   - Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
   - Select your app from the dropdown
   - Click "Generate Access Token"
   - Grant necessary permissions:
     - `pages_manage_posts`
     - `pages_read_engagement`
     - `pages_show_list`
   - Copy the short-lived token (you'll extend it next)

4. **Get Long-Lived Page Access Token:**
   
   **Option A: Using Graph API Explorer (Easiest)**
   - In Graph API Explorer, select your app
   - Click "Generate Access Token" → "Generate Long-Lived Token"
   - Select your page from the dropdown
   - Copy the long-lived token (valid for ~60 days)
   
   **Option B: Using API Call (Manual)**
   - First, exchange user token for long-lived user token:
     ```
     GET https://graph.facebook.com/v19.0/oauth/access_token?
       grant_type=fb_exchange_token&
       client_id={APP_ID}&
       client_secret={APP_SECRET}&
       fb_exchange_token={SHORT_LIVED_TOKEN}
     ```
   - Then, get page access token:
     ```
     GET https://graph.facebook.com/v19.0/me/accounts?
       access_token={LONG_LIVED_USER_TOKEN}
     ```
   - Copy the `access_token` from the response

5. **Get Page ID:**
   - Go to your Facebook Page
   - Click "About" → "Page ID" (or check page settings)
   - Alternatively, use Graph API:
     ```
     GET https://graph.facebook.com/v19.0/me/accounts?
       access_token={PAGE_ACCESS_TOKEN}
     ```
   - Find your page and copy the `id` field

### 2. GitHub Secrets Setup

1. **Go to your GitHub repository**
2. **Navigate to:** Settings → Secrets and variables → Actions
3. **Click "New repository secret"**
4. **Add the following secrets:**
   - **Name:** `FB_PAGE_ID`
     - **Value:** Your Facebook Page ID (from step 1.5)
   - **Name:** `FB_PAGE_TOKEN`
     - **Value:** Your long-lived Page Access Token (from step 1.4)

### 3. Local Testing (Optional)

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd "Sweden Protidin"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   
   **Windows (PowerShell):**
   ```powershell
   $env:FB_PAGE_ID="your_page_id"
   $env:FB_PAGE_TOKEN="your_page_token"
   ```
   
   **Linux/Mac:**
   ```bash
   export FB_PAGE_ID="your_page_id"
   export FB_PAGE_TOKEN="your_page_token"
   ```

4. **Run the bot:**
   ```bash
   python newsbot/main.py
   ```

## How It Works

1. **RSS Fetching:** Reads RSS feed URLs from `newsbot/rss_list.json`
2. **Article Processing:** Parses headlines, descriptions, and links
3. **Duplicate Check:** Skips articles already in `newsbot/posted.json`
4. **Translation:** Translates titles and summaries to Bangla using googletrans
5. **Summary Creation:** Creates 3-bullet point summaries from article descriptions
6. **Facebook Posting:** Formats and posts to Facebook Page via Graph API
7. **Tracking:** Saves posted article GUIDs to avoid duplicates

## Post Format

```
📰 শিরোনাম: [Bangla translated title]

📌 সংক্ষেপ:
- [Summary point 1]
- [Summary point 2]
- [Summary point 3]

🔗 সূত্র: [Original article link]
```

## GitHub Actions Schedule

The workflow runs daily at **08:00 Sweden time** (07:00 UTC in winter, 06:00 UTC in summer).

To manually trigger:
- Go to Actions tab in GitHub
- Select "Daily News Post to Facebook"
- Click "Run workflow"

## Customization

### Add More RSS Feeds

Edit `newsbot/rss_list.json`:
```json
[
  "https://www.svt.se/nyheter/rss.xml",
  "https://feeds.expressen.se/nyheter/",
  "https://www.aftonbladet.se/rss.xml",
  "https://your-feed-url.com/rss.xml"
]
```

### Change Schedule

Edit `.github/workflows/post.yml`:
```yaml
schedule:
  - cron: '0 7 * * *'  # Change time (UTC)
```

Cron format: `minute hour day month weekday`

### Modify Post Format

Edit the `format_facebook_post()` function in `newsbot/main.py`.

## Troubleshooting

### Translation Errors
- googletrans may have rate limits or temporary issues
- The bot will fallback to original text if translation fails
- Check logs for translation warnings

### Facebook API Errors
- Verify Page Access Token is valid and not expired
- Ensure token has `pages_manage_posts` permission
- Check Facebook Page ID is correct
- Review logs for specific API error messages

### Duplicate Posts
- Clear `newsbot/posted.json` to reset posted articles database
- Or manually remove specific GUIDs from the file

### GitHub Actions Not Running
- Check workflow file syntax
- Verify secrets are set correctly
- Check Actions tab for error logs
- Ensure workflow is enabled in repository settings

## Dependencies

- `feedparser` - RSS feed parsing
- `googletrans==4.0.0-rc1` - Free Google Translate API
- `requests` - HTTP requests for Facebook API

## License

This project is open source and available for personal use.

## Notes

- ⚠️ **Rate Limiting:** The bot includes a 2-second delay between posts to avoid rate limits
- ⚠️ **Token Expiry:** Long-lived tokens expire after ~60 days. You'll need to regenerate and update the secret
- ⚠️ **Translation Quality:** googletrans is free but may have occasional service interruptions
- ⚠️ **RSS Feed Availability:** Some feeds may be temporarily unavailable

## Support

For issues or questions:
1. Check the logs in GitHub Actions
2. Review Facebook Graph API documentation
3. Verify all secrets are correctly set

---

**Made with ❤️ for the Swedish-Bangla community**

