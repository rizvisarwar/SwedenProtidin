"""
Summary generation module following SOLID principles.
Provides abstract interface for text summarization.
"""
from abc import ABC, abstractmethod
from typing import Optional
import os


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


class OpenAISummaryGenerator(SummaryGenerator):
    """
    Abstractive summarization using OpenAI GPT models.
    Produces natural, human-like summaries that are more engaging than extractive methods.
    """
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: str = None, max_tokens: int = 150, output_language: str = None):
        """
        Initialize OpenAI summarizer.
        
        Args:
            model: OpenAI model to use ('gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo-preview')
            api_key: OpenAI API key (if None, uses OPENAI_API_KEY env var)
            max_tokens: Maximum tokens in summary (default: 150 for ~2-3 sentences)
            output_language: Target language for summary (e.g., 'bn' for Bangla, 'sv' for Swedish)
                           If None, summary will be in the same language as input
        """
        self.model = model
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.max_tokens = max_tokens
        self.output_language = output_language
        
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
    
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate abstractive summary using OpenAI GPT.
        
        Args:
            text: Input text to summarize
            max_sentences: Target number of sentences (used to estimate max_tokens)
            
        Returns:
            Natural, engaging summary text
        """
        if not text or not text.strip():
            return ""
        
        try:
            import requests
            
            # Truncate text if too long (GPT-3.5-turbo has 16k context, but we want to keep it reasonable)
            # Keep first ~3000 characters to ensure we get the main content
            if len(text) > 3000:
                text = text[:3000] + "..."
            
            # Adjust max_tokens based on max_sentences (roughly 50 tokens per sentence)
            target_tokens = min(self.max_tokens, max_sentences * 50)
            
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Build prompt based on output language
            if self.output_language == 'bn':
                # Generate summary directly in Bangla
                system_message = "You are an expert at summarizing news articles in an engaging way. Always respond in Bangla (Bengali) language."
                prompt = f"""নিম্নলিখিত সংবাদ নিবন্ধটি একটি আকর্ষণীয় এবং সহজে পড়া যায় এমন উপায়ে সংক্ষিপ্ত করুন। 
সবচেয়ে গুরুত্বপূর্ণ পয়েন্টগুলিতে ফোকাস করুন এবং সারসংক্ষেপটি পাঠকদের জন্য আকর্ষণীয় করুন।
স্পষ্ট এবং সহজ ভাষা ব্যবহার করুন।

নিবন্ধ:
{text}

সারসংক্ষেপ:"""
            else:
                # Generate summary in Swedish (default)
                system_message = "Du är en expert på att sammanfatta nyhetsartiklar på ett engagerande sätt."
                prompt = f"""Sammanfatta följande nyhetsartikel på ett engagerande och lättläst sätt. 
Fokusera på de viktigaste punkterna och gör sammanfattningen intressant för läsare.
Använd klart och tydligt språk.

Artikel:
{text}

Sammanfattning:"""
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": target_tokens,
                "temperature": 0.7,  # Slightly creative for more engaging summaries
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            summary = result['choices'][0]['message']['content'].strip()
            
            return summary
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"OpenAI summarization error: {e}")
            # Fallback to extractive method
            fallback = SumySummaryGenerator(language='sv')
            return fallback.summarize(text, max_sentences)


class HuggingFaceSummaryGenerator(SummaryGenerator):
    """
    Abstractive summarization using Hugging Face transformers.
    Uses Swedish or multilingual models for better quality summaries.
    Free and runs locally, but requires more computational resources.
    """
    
    def __init__(self, model_name: str = "KBLab/sentence-bert-swedish-cased", use_abstractive: bool = True):
        """
        Initialize Hugging Face summarizer.
        
        Args:
            model_name: Hugging Face model name
                      Options:
                      - "KBLab/sentence-bert-swedish-cased" (Swedish BERT, extractive)
                      - "facebook/bart-large-cnn" (English, abstractive, good quality)
                      - "google/mt5-base" (Multilingual, abstractive)
            use_abstractive: If True, use abstractive models (BART, T5). If False, use extractive.
        """
        self.model_name = model_name
        self.use_abstractive = use_abstractive
        self._model = None
        self._tokenizer = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of model and tokenizer."""
        if self._initialized:
            return
        
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
            
            if self.use_abstractive:
                # Use abstractive summarization pipeline
                self._summarizer = pipeline(
                    "summarization",
                    model=self.model_name,
                    tokenizer=self.model_name,
                    device=-1  # Use CPU (-1) or GPU (0, 1, etc.)
                )
            else:
                # For extractive, we'd need a different approach
                # For now, fall back to abstractive
                self._summarizer = pipeline(
                    "summarization",
                    model="facebook/bart-large-cnn",
                    device=-1
                )
            
            self._initialized = True
            
        except ImportError:
            raise ImportError(
                "transformers library not installed. Install with: pip install transformers torch"
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to initialize Hugging Face model: {e}")
            raise
    
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate abstractive summary using Hugging Face transformers.
        
        Args:
            text: Input text to summarize
            max_sentences: Target number of sentences (used to estimate max_length)
            
        Returns:
            Natural summary text
        """
        if not text or not text.strip():
            return ""
        
        try:
            self._initialize()
            
            # Estimate max_length based on target sentences (roughly 50 tokens per sentence)
            max_length = min(150, max_sentences * 50)
            min_length = max(30, max_sentences * 20)
            
            # Truncate if too long (most models have token limits)
            # BART can handle ~1024 tokens, so keep text reasonable
            if len(text) > 2000:
                text = text[:2000]
            
            result = self._summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=True,
                temperature=0.7,
                truncation=True
            )
            
            summary = result[0]['summary_text'].strip()
            return summary
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Hugging Face summarization error: {e}")
            # Fallback to extractive method
            fallback = SumySummaryGenerator(language='sv')
            return fallback.summarize(text, max_sentences)


class TextRankSummaryGenerator(SummaryGenerator):
    """
    Alternative extractive summarizer using TextRank algorithm.
    Sometimes produces better results than LexRank for news articles.
    """
    
    def __init__(self, language: str = 'sv'):
        """Initialize TextRank summarizer."""
        self.language = language
        self._summarizer = None
        self._parser = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize TextRank components."""
        try:
            from sumy.parsers.plaintext import PlaintextParser
            from sumy.nlp.tokenizers import Tokenizer
            from sumy.summarizers.text_rank import TextRankSummarizer
            
            self._parser_class = PlaintextParser
            self._tokenizer_class = Tokenizer
            self._summarizer_class = TextRankSummarizer
            self._initialized = True
        except ImportError:
            self._initialized = False
    
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """Generate summary using TextRank algorithm."""
        if not self._initialized:
            # Fallback to LexRank
            fallback = SumySummaryGenerator(language=self.language)
            return fallback.summarize(text, max_sentences)
        
        if not text or not text.strip():
            return ""
        
        try:
            # Reuse cleaning logic from SumySummaryGenerator
            base_generator = SumySummaryGenerator(language=self.language)
            cleaned_text = base_generator._clean_text(text)
            
            if not cleaned_text:
                return ""
            
            parser = self._parser_class.from_string(
                cleaned_text,
                self._tokenizer_class(self.language)
            )
            
            doc_sentences = len(parser.document.sentences)
            if doc_sentences < 3:
                return base_generator.summarize(text, max_sentences)
            
            optimal_sentences = min(max_sentences, max(2, int(doc_sentences * 0.15)))
            
            summarizer = self._summarizer_class()
            summary_sentences = summarizer(parser.document, optimal_sentences)
            
            summary_parts = []
            for sentence in summary_sentences:
                sentence_str = str(sentence).strip()
                if sentence_str:
                    sentence_str = sentence_str.replace('\n', ' ').replace('\r', ' ')
                    sentence_str = ' '.join(sentence_str.split())
                    if not sentence_str[-1] in '.!?':
                        sentence_str += '.'
                    summary_parts.append(sentence_str)
            
            summary = ' '.join(summary_parts)
            summary = summary.replace('\n', ' ').replace('\r', ' ')
            
            import re
            summary = re.sub(r'\.([A-ZÅÄÖ])', r'. \1', summary)
            summary = ' '.join(summary.split())
            
            return summary.strip()
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"TextRank summarization error: {e}")
            fallback = SumySummaryGenerator(language=self.language)
            return fallback.summarize(text, max_sentences)


def create_summarizer(summarizer_type: str = "sumy", **kwargs) -> SummaryGenerator:
    """
    Factory function to create summary generators.
    Follows Open/Closed Principle - easy to extend with new summarizer types.
    
    Args:
        summarizer_type: Type of summarizer:
            - 'sumy': LexRank extractive (current default)
            - 'textrank': TextRank extractive (alternative extractive)
            - 'openai': OpenAI GPT abstractive (best quality, requires API key)
            - 'huggingface': Hugging Face transformers abstractive (free, local)
            - 'simple': Simple rule-based fallback
        **kwargs: Additional arguments for summarizer
        
    Returns:
        SummaryGenerator instance
    """
    if summarizer_type == "sumy":
        return SumySummaryGenerator(**kwargs)
    elif summarizer_type == "textrank":
        return TextRankSummaryGenerator(**kwargs)
    elif summarizer_type == "openai":
        return OpenAISummaryGenerator(**kwargs)
    elif summarizer_type == "huggingface":
        return HuggingFaceSummaryGenerator(**kwargs)
    elif summarizer_type == "simple":
        return SimpleSummaryGenerator()
    else:
        raise ValueError(f"Unknown summarizer type: {summarizer_type}. Options: 'sumy', 'textrank', 'openai', 'huggingface', 'simple'")


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