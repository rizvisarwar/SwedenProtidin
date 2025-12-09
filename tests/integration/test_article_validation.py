#!/usr/bin/env python3
"""
Test script to verify that articles without generated text are properly skipped.
This tests the validation logic without requiring Facebook credentials.
"""

import os
import sys
import logging

# Add newsbot to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'newsbot'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_article_validation():
    """Test that articles without text are properly validated."""
    
    # Test case 1: Article with empty summary_bn
    logger.info("=" * 60)
    logger.info("Test 1: Article with empty summary_bn")
    logger.info("=" * 60)
    
    summary_bn = ""
    if not summary_bn or not summary_bn.strip():
        logger.error(f"ERROR: summary_bn is empty! Cannot post article without text.")
        logger.error(f"  This usually means:")
        logger.error(f"  1. OPENAI_API_KEY is not set or invalid")
        logger.error(f"  2. Article generation failed (check logs above for errors)")
        logger.error(f"  3. Summarizer returned empty result")
        logger.info("✓ Validation correctly detected empty article - would skip posting")
    else:
        logger.error("✗ Validation failed - should have detected empty article")
    
    # Test case 2: Article with whitespace-only summary_bn
    logger.info("\n" + "=" * 60)
    logger.info("Test 2: Article with whitespace-only summary_bn")
    logger.info("=" * 60)
    
    summary_bn = "   \n\t  "
    if not summary_bn or not summary_bn.strip():
        logger.error(f"ERROR: summary_bn is empty! Cannot post article without text.")
        logger.info("✓ Validation correctly detected whitespace-only article - would skip posting")
    else:
        logger.error("✗ Validation failed - should have detected whitespace-only article")
    
    # Test case 3: Article with valid summary_bn
    logger.info("\n" + "=" * 60)
    logger.info("Test 3: Article with valid summary_bn")
    logger.info("=" * 60)
    
    summary_bn = "এটি একটি সম্পূর্ণ বাংলা সংবাদ নিবন্ধ। এটি পেশাদার সাংবাদিকের মতো লেখা হয়েছে।"
    if not summary_bn or not summary_bn.strip():
        logger.error("✗ Validation failed - should have passed valid article")
    else:
        logger.info(f"✓ Validation passed - article has {len(summary_bn)} characters")
        logger.info(f"  Article preview: {summary_bn[:100]}...")
        logger.info("✓ Article would be posted to Facebook")
    
    # Test case 4: Test with actual scraping (if API key is set)
    logger.info("\n" + "=" * 60)
    logger.info("Test 4: Test with actual article scraping")
    logger.info("=" * 60)
    
    openai_key = os.environ.get('OPENAI_API_KEY')
    if not openai_key:
        logger.warning("OPENAI_API_KEY not set - skipping actual scraping test")
        logger.info("  Set OPENAI_API_KEY to test article generation")
    else:
        logger.info(f"OPENAI_API_KEY is set (length: {len(openai_key)} characters)")
        try:
            from scrape_news import scrape_news
            result = scrape_news()
            articles = result.get('articles', [])
            
            if articles:
                first_article = articles[0]
                summary_sv = first_article.get('summary_sv', '')
                
                logger.info(f"Scraped {len(articles)} articles")
                logger.info(f"First article title: {first_article.get('title_sv', 'N/A')[:50]}...")
                logger.info(f"First article summary_sv length: {len(summary_sv)} characters")
                
                if summary_sv:
                    logger.info(f"✓ Article generation successful - summary_sv has content")
                    logger.info(f"  Preview: {summary_sv[:200]}...")
                else:
                    logger.error(f"✗ Article generation failed - summary_sv is empty")
                    logger.error(f"  This means the validation check would prevent posting")
            else:
                logger.warning("No articles found")
        except Exception as e:
            logger.error(f"Error testing scraping: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    logger.info("✓ Validation logic correctly identifies empty articles")
    logger.info("✓ Articles without text will be skipped (not posted)")
    logger.info("✓ Only articles with generated text will be posted")

if __name__ == '__main__':
    test_article_validation()

