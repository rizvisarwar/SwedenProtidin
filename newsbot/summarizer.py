"""
Summary generation module following SOLID principles.
Provides abstract interface for text summarization.
"""
from abc import ABC, abstractmethod
from typing import Optional


class SummaryGenerator(ABC):
    """
    Abstract base class for text summarization.
    Follows Dependency Inversion Principle - depend on abstraction.
    """
    
    @abstractmethod
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate summary from text.
        
        Args:
            text: Input text to summarize
            max_sentences: Maximum number of sentences in summary
            
        Returns:
            Summary text
        """
        pass


class SumySummaryGenerator(SummaryGenerator):
    """
    Concrete implementation using Sumy library for extractive summarization.
    Follows Single Responsibility Principle - only handles Sumy-based summarization.
    """
    
    def __init__(self, language: str = 'sv'):
        """
        Initialize Sumy summarizer.
        
        Args:
            language: ISO 639-1 language code for summarization (default: 'sv' for Swedish)
                      Examples: 'sv' (Swedish), 'en' (English), 'de' (German)
        """
        self.language = language
        self._summarizer = None
        self._parser = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Sumy components lazily to avoid import errors if not installed."""
        try:
            from sumy.parsers.plaintext import PlaintextParser
            from sumy.nlp.tokenizers import Tokenizer
            # Use LexRank - better quality than LSA for news articles
            from sumy.summarizers.lex_rank import LexRankSummarizer
            
            self._parser_class = PlaintextParser
            self._tokenizer_class = Tokenizer
            self._summarizer_class = LexRankSummarizer
            self._initialized = True
        except ImportError:
            self._initialized = False
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and preprocess text before summarization.
        Removes noise, dates, author info, and improves quality.
        """
        if not text:
            return ""
        
        import re
        
        # Remove common noise patterns
        # Remove date patterns like "2025 12 08" or "2025-12-08" only if they're standalone
        # (on their own line or surrounded by whitespace/newlines) to avoid corrupting content
        # First, remove dates that are on their own line (most common noise pattern)
        text = re.sub(r'^\d{4}[\s\-]\d{1,2}[\s\-]\d{1,2}\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n\d{4}[\s\-]\d{1,2}[\s\-]\d{1,2}\n', '\n', text)
        text = re.sub(r'\n\d{4}[\s\-]\d{1,2}[\s\-]\d{1,2}\s+', '\n', text)
        text = re.sub(r'\s+\d{4}[\s\-]\d{1,2}[\s\-]\d{1,2}\n', '\n', text)
        
        # Remove standalone year numbers only if they're on their own line
        # This prevents removing years that are part of sentences like "founded in 2025"
        text = re.sub(r'^\b\d{4}\b\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n\b\d{4}\b\n', '\n', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Remove all newline characters and replace with spaces
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Ensure sentences end with proper punctuation
        # Split by sentence endings, but preserve the punctuation
        sentences = re.split(r'([.!?])\s+', text)
        cleaned_sentences = []
        
        for i in range(0, len(sentences), 2):
            if i < len(sentences):
                sentence = sentences[i].strip()
                if sentence and len(sentence) > 20:
                    # Add punctuation if missing
                    if i + 1 < len(sentences) and sentences[i + 1]:
                        cleaned_sentences.append(sentence + sentences[i + 1])
                    elif not sentence[-1] in '.!?':
                        cleaned_sentences.append(sentence + '.')
                    else:
                        cleaned_sentences.append(sentence)
        
        return ' '.join(cleaned_sentences) if cleaned_sentences else text
    
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate extractive summary using Sumy LexRank algorithm.
        LexRank is better than LSA for news articles as it uses graph-based ranking.
        
        Args:
            text: Input text to summarize
            max_sentences: Maximum number of sentences in summary (default: 3-4 recommended)
            
        Returns:
            Summary text, or original text if summarization fails
        """
        if not self._initialized:
            return self._fallback_summary(text, max_sentences)
        
        if not text or not text.strip():
            return ""
        
        try:
            # Clean text first
            cleaned_text = self._clean_text(text)
            if not cleaned_text:
                return self._fallback_summary(text, max_sentences)
            
            # Parse text
            parser = self._parser_class.from_string(
                cleaned_text,
                self._tokenizer_class(self.language)
            )
            
            # Calculate optimal sentence count based on document length
            doc_sentences = len(parser.document.sentences)
            if doc_sentences < 3:
                # Very short text, use fallback
                return self._fallback_summary(text, max_sentences)
            
            # Adjust max_sentences: use 10-15% of document or max_sentences, whichever is smaller
            optimal_sentences = min(max_sentences, max(2, int(doc_sentences * 0.15)))
            
            # Generate summary
            summarizer = self._summarizer_class()
            summary_sentences = summarizer(parser.document, optimal_sentences)
            
            # Join sentences with proper punctuation
            summary_parts = []
            for sentence in summary_sentences:
                sentence_str = str(sentence).strip()
                if sentence_str:
                    # Remove all newlines and replace with spaces
                    sentence_str = sentence_str.replace('\n', ' ').replace('\r', ' ')
                    # Remove multiple spaces
                    sentence_str = ' '.join(sentence_str.split())
                    # Ensure sentence ends with punctuation
                    if not sentence_str[-1] in '.!?':
                        sentence_str += '.'
                    summary_parts.append(sentence_str)
            
            # Join with space (sentences already have punctuation)
            summary = ' '.join(summary_parts)
            
            # Remove all newline characters (replace with spaces)
            summary = summary.replace('\n', ' ').replace('\r', ' ')
            
            # Final cleanup: ensure proper spacing and punctuation
            import re
            # Add space after dot if missing (before capital letters)
            summary = re.sub(r'\.([A-ZÅÄÖ])', r'. \1', summary)
            
            # Detect sentence boundaries: capital letter after lowercase (likely new sentence)
            # Add dot before capital letters that start new sentences
            summary = re.sub(r'([a-zåäö])\s+([A-ZÅÄÖ][a-zåäö])', r'\1. \2', summary)
            
            # Ensure proper spacing after all punctuation
            summary = re.sub(r'([.!?])([A-ZÅÄÖa-zåäö])', r'\1 \2', summary)
            
            # Remove multiple spaces
            summary = ' '.join(summary.split())
            
            return summary.strip()
            
        except Exception as e:
            # Fallback to simple summarization on error
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Summarization error: {e}, using fallback")
            return self._fallback_summary(text, max_sentences)
    
    def _fallback_summary(self, text: str, max_sentences: int) -> str:
        """
        Fallback simple summarization if Sumy is not available or fails.
        
        Args:
            text: Input text
            max_sentences: Maximum sentences
            
        Returns:
            Simple summary with proper punctuation
        """
        if not text:
            return ""
        
        import re
        
        # Remove newlines
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = ' '.join(text.split())
        
        # Simple sentence splitting
        sentences = re.split(r'([.!?])\s+', text)
        summary_parts = []
        
        for i in range(0, len(sentences), 2):
            if i < len(sentences):
                sentence = sentences[i].strip()
                if sentence and len(sentence) > 20:
                    # Add punctuation if present in split
                    if i + 1 < len(sentences) and sentences[i + 1] in '.!?':
                        sentence += sentences[i + 1]
                    elif not sentence[-1] in '.!?':
                        sentence += '.'
                    summary_parts.append(sentence)
                    if len(summary_parts) >= max_sentences:
                        break
        
        # Join with spaces and ensure proper formatting
        summary = ' '.join(summary_parts)
        # Remove multiple spaces
        summary = ' '.join(summary.split())
        
        return summary.strip()


def create_summarizer(summarizer_type: str = "sumy", **kwargs) -> SummaryGenerator:
    """
    Factory function to create summary generators.
    Follows Open/Closed Principle - easy to extend with new summarizer types.
    
    Args:
        summarizer_type: Type of summarizer ('sumy' or 'simple')
        **kwargs: Additional arguments for summarizer
        
    Returns:
        SummaryGenerator instance
    """
    if summarizer_type == "sumy":
        return SumySummaryGenerator(**kwargs)
    elif summarizer_type == "simple":
        return SimpleSummaryGenerator()
    else:
        raise ValueError(f"Unknown summarizer type: {summarizer_type}")


class SimpleSummaryGenerator(SummaryGenerator):
    """
    Simple rule-based summarizer as fallback.
    Follows Single Responsibility Principle.
    """
    
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """
        Simple extractive summary using first N sentences.
        
        Args:
            text: Input text
            max_sentences: Maximum sentences
            
        Returns:
            Summary text
        """
        if not text:
            return ""
        
        import re
        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        summary_sentences = sentences[:max_sentences]
        return " ".join(summary_sentences)