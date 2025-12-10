# PowerShell script to set environment variables for the Swedish News Bot
# Run this script with: .\scripts\set_env_vars.ps1

# Current configuration
$FB_PAGE_ID = "880794241790973"
$FB_PAGE_TOKEN = "EAAWDMjfh2ycBQPvWMl7685aSr7M0AyQIDZC2B35b7OgNemW5fbveqnZBPSeIFtFBiMZASpbZAXgzccTt1tBFz4EkuLs22ibAaZAAzKZB3k7fWKu9peN8pu2ViiWYqmM9q1fw7sNB4HgDMvQ52LFDjdCJhOKjSEi9YqZBfb2y5CGUkKl5J6UECfLEs2jcAcHEtyIoWtSvAu2YZByo4BW2VgZDZD"

# Set environment variables for current session
$env:FB_PAGE_ID = $FB_PAGE_ID
$env:FB_PAGE_TOKEN = $FB_PAGE_TOKEN

Write-Host "Environment variables set for current PowerShell session:" -ForegroundColor Green
Write-Host "  FB_PAGE_ID = $FB_PAGE_ID" -ForegroundColor Cyan
Write-Host "  FB_PAGE_TOKEN = [SET]" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: These variables are only set for this session." -ForegroundColor Yellow
Write-Host "To set them permanently, use the User Environment Variables method." -ForegroundColor Yellow
Write-Host "See docs/ENVIRONMENT_SETUP.md for details." -ForegroundColor Yellow

