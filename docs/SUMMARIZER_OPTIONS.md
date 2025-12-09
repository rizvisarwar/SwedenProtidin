# Summarizer Options Guide

The news bot supports multiple summarization methods. Choose the one that best fits your needs for quality, cost, and performance.

## Available Summarizers

### 1. **Sumy (LexRank)** - Current Default
- **Type**: `"sumy"`
- **Quality**: ⭐⭐⭐ (Good for extractive)
- **Cost**: Free
- **Speed**: Fast
- **Dependencies**: Already installed (`sumy`)
- **Best for**: Quick, reliable summaries when quality is acceptable

**Configuration:**
```json
{
  "summarizer": {
    "type": "sumy",
    "language": "sv",
    "max_sentences": 4
  }
}
```

---

### 2. **TextRank** - Alternative Extractive
- **Type**: `"textrank"`
- **Quality**: ⭐⭐⭐ (Slightly better than LexRank for some articles)
- **Cost**: Free
- **Speed**: Fast
- **Dependencies**: Already installed (`sumy`)
- **Best for**: Trying a different extractive algorithm

**Configuration:**
```json
{
  "summarizer": {
    "type": "textrank",
    "language": "sv",
    "max_sentences": 4
  }
}
```

---

### 3. **OpenAI GPT** - Best Quality ⭐⭐⭐⭐⭐
- **Type**: `"openai"`
- **Quality**: ⭐⭐⭐⭐⭐ (Natural, engaging, abstractive summaries)
- **Cost**: ~$0.001-0.002 per article (very affordable)
- **Speed**: Fast (API call)
- **Dependencies**: None (uses `requests` which is already installed)
- **Best for**: Professional, engaging summaries that read naturally

**Setup:**
1. Get OpenAI API key from https://platform.openai.com/api-keys
2. Set environment variable:
   ```bash
   export OPENAI_API_KEY="sk-your-key-here"
   ```
   Or on Windows:
   ```powershell
   $env:OPENAI_API_KEY="sk-your-key-here"
   ```

**Configuration:**
```json
{
  "summarizer": {
    "type": "openai",
    "max_sentences": 3
  }
}
```

**Models available:**
- `gpt-3.5-turbo` (default, recommended, cheapest)
- `gpt-4` (better quality, more expensive)
- `gpt-4-turbo-preview` (latest, best quality)

To use a different model, modify `newsbot/summarizer.py` line ~330:
```python
def __init__(self, model: str = "gpt-4", ...):  # Change default model
```

**Cost estimate:**
- GPT-3.5-turbo: ~$0.001 per article
- GPT-4: ~$0.01-0.02 per article
- For 4 posts/day: ~$0.004-0.008/day with GPT-3.5-turbo

---

### 4. **Hugging Face Transformers** - Free & Local ⭐⭐⭐⭐
- **Type**: `"huggingface"`
- **Quality**: ⭐⭐⭐⭐ (Very good abstractive summaries)
- **Cost**: Free (runs locally)
- **Speed**: Slower (especially on CPU, faster with GPU)
- **Dependencies**: Requires installation
- **Best for**: Free, high-quality summaries without API costs

**Installation:**
```bash
pip install transformers torch sentencepiece
```

**Configuration:**
```json
{
  "summarizer": {
    "type": "huggingface",
    "max_sentences": 3
  }
}
```

**Models available:**
- `"facebook/bart-large-cnn"` (default, English, excellent quality)
- `"google/mt5-base"` (multilingual, supports Swedish)
- `"KBLab/sentence-bert-swedish-cased"` (Swedish-specific)

To use a different model, modify `newsbot/summarizer.py` line ~380:
```python
def __init__(self, model_name: str = "google/mt5-base", ...):  # Use multilingual model
```

**Performance:**
- CPU: ~5-10 seconds per article
- GPU: ~1-2 seconds per article

---

## How to Switch Summarizers

1. **Edit `newsbot/config.json`:**
   ```json
   {
     "summarizer": {
       "type": "openai",  // Change this to: "sumy", "textrank", "openai", or "huggingface"
       "language": "sv",
       "max_sentences": 4
     }
   }
   ```

2. **If using OpenAI:**
   - Set `OPENAI_API_KEY` environment variable
   - No code changes needed

3. **If using Hugging Face:**
   - Install dependencies: `pip install transformers torch sentencepiece`
   - No code changes needed

4. **Restart the bot** - it will automatically use the new summarizer

---

## Quality Comparison

| Summarizer | Type | Quality | Naturalness | Cost | Speed |
|------------|------|---------|-------------|------|-------|
| Sumy (LexRank) | Extractive | ⭐⭐⭐ | ⭐⭐ | Free | Fast |
| TextRank | Extractive | ⭐⭐⭐ | ⭐⭐ | Free | Fast |
| OpenAI GPT | Abstractive | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Low | Fast |
| Hugging Face | Abstractive | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Free | Medium |

---

## Recommendations

### For Best Quality (Recommended):
**Use OpenAI GPT-3.5-turbo**
- Natural, engaging summaries
- Very affordable (~$0.001 per article)
- Easy to set up
- Professional results

### For Free High Quality:
**Use Hugging Face BART**
- Excellent abstractive summaries
- No API costs
- Requires more setup and computational resources

### For Quick Testing:
**Try TextRank first**
- Easy switch from LexRank
- No additional setup
- May produce better results for some articles

---

## Example Output Comparison

**Original Article (excerpt):**
> "Energidryckproducenten Celsius växer så det knakar. Från 2022 till 2023 ökade omsättningen med nästan 100 miljoner kronor. Nu kommer nästa glädjebesked. Framgångssagan fortsätter för Celsius som fortsatte att växa under 2024."

**LexRank (Extractive):**
> "Energidryckproducenten Celsius växer så det knakar. Från 2022 till 2023 ökade omsättningen med nästan 100 miljoner kronor. Nu kommer nästa glädjebesked."

**OpenAI GPT (Abstractive):**
> "Celsius fortsätter sin imponerande tillväxt med nästan 100 miljoner kronor i ökad omsättning mellan 2022 och 2023. Företaget ser fram emot ytterligare positiva utvecklingar efter en framgångsrik 2024."

Notice how the OpenAI version is more natural and engaging while maintaining the key information!

