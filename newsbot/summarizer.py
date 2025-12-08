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
            from sumy.summarizers.lsa import LsaSummarizer
            
            self._parser_class = PlaintextParser
            self._tokenizer_class = Tokenizer
            self._summarizer_class = LsaSummarizer
            self._initialized = True
        except ImportError:
            self._initialized = False
    
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate extractive summary using Sumy LSA algorithm.
        
        Args:
            text: Input text to summarize
            max_sentences: Maximum number of sentences in summary
            
        Returns:
            Summary text, or original text if summarization fails
        """
        if not self._initialized:
            return self._fallback_summary(text, max_sentences)
        
        if not text or not text.strip():
            return ""
        
        try:
            # Parse text
            parser = self._parser_class.from_string(
                text,
                self._tokenizer_class(self.language)
            )
            
            # Generate summary
            summarizer = self._summarizer_class()
            summary_sentences = summarizer(parser.document, max_sentences)
            
            # Join sentences
            summary = " ".join(str(sentence) for sentence in summary_sentences)
            return summary.strip()
            
        except Exception:
            # Fallback to simple summarization on error
            return self._fallback_summary(text, max_sentences)
    
    def _fallback_summary(self, text: str, max_sentences: int) -> str:
        """
        Fallback simple summarization if Sumy is not available or fails.
        
        Args:
            text: Input text
            max_sentences: Maximum sentences
            
        Returns:
            Simple summary
        """
        if not text:
            return ""
        
        # Simple sentence splitting
        import re
        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Take first N sentences
        summary_sentences = sentences[:max_sentences]
        return " ".join(summary_sentences)


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

