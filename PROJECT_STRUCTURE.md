# Project Structure

This document describes the organized structure of the Sweden Protidin news bot project.

## Directory Structure

```
.
├── newsbot/              # Main application code
│   ├── main.py          # Main bot script
│   ├── scrape_news.py   # News scraping module
│   ├── summarizer.py    # Summarization module
│   ├── config.json      # Configuration file
│   └── posted.json      # Posted articles database
│
├── tests/               # All test files
│   ├── unit/            # Unit tests
│   │   └── test_translate.py
│   ├── integration/     # Integration tests
│   │   ├── test_bangla_output.py
│   │   ├── test_openai_summarizer.py
│   │   └── test_scraped_text.py
│   └── output/          # Test output files (gitignored)
│
├── docs/                # Documentation
│   ├── FIX_PERMISSIONS.md
│   ├── SETUP.md
│   ├── SUMMARIZER_OPTIONS.md
│   └── TEST_BANGLA_USAGE.md
│
├── scripts/             # Utility scripts
│   └── check_openai_key.py
│
├── .github/             # GitHub Actions workflows
├── README.md            # Main project documentation
├── requirements.txt     # Python dependencies
└── pytest.ini          # Pytest configuration
```

## Running Tests

### Integration Tests

From the project root:

```bash
# Test Bangla output
python tests/integration/test_bangla_output.py

# Test scraped text
python tests/integration/test_scraped_text.py

# Test OpenAI summarizer
python tests/integration/test_openai_summarizer.py
```

### Unit Tests

```bash
pytest tests/unit/
```

## Utility Scripts

```bash
# Check OpenAI API key
python scripts/check_openai_key.py
```

## Notes

- Test output files are automatically saved to `tests/output/` and are gitignored
- All test scripts have been updated with correct import paths
- Documentation is organized in the `docs/` directory

