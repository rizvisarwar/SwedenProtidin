# Tests

This directory contains unit tests for the newsbot project.

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=newsbot --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_translate.py
```

### Run specific test:
```bash
pytest tests/test_translate.py::TestTranslateText::test_translate_text_success
```

### Run with verbose output:
```bash
pytest -v
```

## Test Structure

- `test_translate.py` - Unit tests for the `translate_text` function

## Requirements

Tests require `pytest` which is included in `requirements.txt`.

