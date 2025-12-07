"""
Unit tests for the translate_text function in newsbot.main
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import newsbot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from newsbot.main import translate_text


class TestTranslateText:
    """Test suite for translate_text function"""
    
    def test_translate_text_success(self):
        """Test successful translation from English to Bangla"""
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.return_value = Mock(text="হ্যালো বিশ্ব")
            result = translate_text("Hello World", dest='bn')
            assert result == "হ্যালো বিশ্ব"
            mock_translator.translate.assert_called_once_with("Hello World", dest='bn')
    
    def test_translate_text_empty_string(self):
        """Test that empty string returns empty string"""
        result = translate_text("", dest='bn')
        assert result == ""
    
    def test_translate_text_whitespace_only(self):
        """Test that whitespace-only string returns empty string"""
        result = translate_text("   \n\t  ", dest='bn')
        assert result == ""
    
    def test_translate_text_none(self):
        """Test that None input returns empty string"""
        result = translate_text(None, dest='bn')
        assert result == ""
    
    def test_translate_text_removes_extra_whitespace(self):
        """Test that extra whitespace is normalized"""
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.return_value = Mock(text="Test")
            result = translate_text("Hello    World\n\nTest", dest='bn')
            # Should normalize whitespace before translation
            mock_translator.translate.assert_called_once()
            call_args = mock_translator.translate.call_args
            assert call_args[0][0] == "Hello World Test"
    
    def test_translate_text_truncates_long_text(self):
        """Test that text longer than 5000 chars is truncated"""
        long_text = "A" * 6000
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.return_value = Mock(text="Translated")
            result = translate_text(long_text, dest='bn')
            mock_translator.translate.assert_called_once()
            call_args = mock_translator.translate.call_args
            # Should be truncated to 5000 chars
            assert len(call_args[0][0]) == 5000
            assert call_args[0][0] == "A" * 5000
    
    def test_translate_text_exactly_5000_chars(self):
        """Test that text exactly 5000 chars is not truncated"""
        text_5000 = "A" * 5000
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.return_value = Mock(text="Translated")
            result = translate_text(text_5000, dest='bn')
            mock_translator.translate.assert_called_once()
            call_args = mock_translator.translate.call_args
            assert len(call_args[0][0]) == 5000
    
    def test_translate_text_translation_failure(self):
        """Test that translation failure returns original text"""
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.side_effect = Exception("Translation failed")
            result = translate_text("Hello World", dest='bn')
            # Should return original text on failure
            assert result == "Hello World"
    
    def test_translate_text_different_dest_language(self):
        """Test translation to different destination language"""
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.return_value = Mock(text="Bonjour")
            result = translate_text("Hello", dest='fr')
            assert result == "Bonjour"
            mock_translator.translate.assert_called_once_with("Hello", dest='fr')
    
    def test_translate_text_swedish_to_bangla(self):
        """Test translation from Swedish to Bangla (real use case)"""
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.return_value = Mock(text="সুইডেনের খবর")
            result = translate_text("Sverige nyheter", dest='bn')
            assert result == "সুইডেনের খবর"
            mock_translator.translate.assert_called_once_with("Sverige nyheter", dest='bn')
    
    def test_translate_text_with_special_characters(self):
        """Test translation with special characters"""
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.return_value = Mock(text="Test & More")
            result = translate_text("Test & More @#$", dest='bn')
            mock_translator.translate.assert_called_once()
            # Should handle special characters
            assert result == "Test & More"
    
    def test_translate_text_multiple_spaces_normalized(self):
        """Test that multiple spaces are normalized to single space"""
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.return_value = Mock(text="Normalized")
            result = translate_text("Text    with     multiple    spaces", dest='bn')
            mock_translator.translate.assert_called_once()
            call_args = mock_translator.translate.call_args
            assert call_args[0][0] == "Text with multiple spaces"
    
    def test_translate_text_newlines_removed(self):
        """Test that newlines are normalized"""
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.return_value = Mock(text="Single line")
            result = translate_text("Line1\nLine2\nLine3", dest='bn')
            mock_translator.translate.assert_called_once()
            call_args = mock_translator.translate.call_args
            assert call_args[0][0] == "Line1 Line2 Line3"
    
    def test_translate_text_unicode_characters(self):
        """Test translation with Unicode characters (Swedish special chars)"""
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.return_value = Mock(text="Translated")
            result = translate_text("Göteborg är vackert", dest='bn')
            mock_translator.translate.assert_called_once()
            call_args = mock_translator.translate.call_args
            assert "Göteborg" in call_args[0][0]
            assert "är" in call_args[0][0]
    
    def test_translate_text_default_dest_bangla(self):
        """Test that default destination is Bangla"""
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.return_value = Mock(text="Translated")
            result = translate_text("Hello")
            mock_translator.translate.assert_called_once_with("Hello", dest='bn')
    
    def test_translate_text_network_error_handling(self):
        """Test handling of network errors during translation"""
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.side_effect = ConnectionError("Network error")
            result = translate_text("Hello World", dest='bn')
            # Should return original text on network error
            assert result == "Hello World"
    
    def test_translate_text_timeout_error_handling(self):
        """Test handling of timeout errors during translation"""
        with patch('newsbot.main.translator') as mock_translator:
            mock_translator.translate.side_effect = TimeoutError("Request timeout")
            result = translate_text("Hello World", dest='bn')
            # Should return original text on timeout
            assert result == "Hello World"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

