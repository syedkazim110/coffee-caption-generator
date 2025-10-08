# ☕ Catchy Coffee Caption Generator

A RAG-based system that generates viral-style coffee captions using trending Google Trends keywords and rich coffee context from articles.

## 🎯 Features

- **RAG-Powered**: Uses Retrieval-Augmented Generation to create contextually rich captions
- **Trending Keywords**: Leverages Google Trends data for current coffee topics
- **Multiple Styles**: 6 different viral caption styles (POV, relatable, trending, etc.)
- **Coffee Context**: Extracts flavor profiles and descriptions from coffee articles
- **Easy CLI**: Simple command-line interface for generating captions

## 🚀 Quick Start

1. **Generate trending keywords:**
   ```bash
   python GetCoffeTrend.py
   ```

2. **Extract coffee context:**
   ```bash
   python coffee_context_extractor.py
   ```

3. **Generate captions:**
   ```bash
   python caption_generator_cli.py
   ```

## 📁 Files Overview

- `GetCoffeTrend.py` - Scrapes Google Trends for coffee keywords
- `coffee_context_extractor.py` - Extracts coffee language from articles
- `rag_caption_generator.py` - Main RAG-based caption generation engine
- `caption_generator_cli.py` - Interactive command-line interface
- `coffee_articles.csv` - Source coffee articles for context
- `trending_coffee_keywords.json` - Generated trending keywords
- `coffee_context.json` - Extracted coffee context

## 🎭 Caption Styles

1. **POV Style**: "POV: You try {keyword} and it's {context} ☕✨"
2. **Relatable**: "Me: I don't need {keyword}. Also me: *orders three* 🤷‍♀️"
3. **Trending Format**: "Everyone's talking about {keyword} and honestly... they're right 🔥"
4. **Descriptive Catchy**: "This {keyword} is {context} and I'm obsessed 😍"
5. **Question Hooks**: "Is it just me or is {keyword} with {context} amazing? 🤔☕"
6. **Experience Based**: "Nothing beats {keyword} that's {context} for the perfect coffee break ☕"

## 📊 Sample Output

```
1. POV: You try nitro coffee and it's rich aroma of freshly brewed coffee ☕✨
   📊 Keyword: nitro coffee
   🎯 Context: rich aroma of freshly brewed coffee
   🎭 Style: pov_style

2. Me: I don't need oat milk latte. Also me: *reads it's chocolate and nut notes* 🤷‍♀️
   📊 Keyword: oat milk latte
   🎯 Context: chocolate and nut notes
   🎭 Style: relatable
```

## 🛠️ Requirements

```bash
pip install pandas pytrends scikit-learn requests beautifulsoup4
```

## 🎨 Usage Examples

### Generate captions for specific keyword:
```python
from rag_caption_generator import RAGCaptionGenerator

generator = RAGCaptionGenerator()
captions = generator.generate_multiple_rag_captions(5, "cold brew")
```

### Generate random trending captions:
```python
captions = generator.generate_multiple_rag_captions(10)
```

### Generate specific style captions:
```python
caption = generator.generate_rag_caption(template_category="pov_style")
```

## 📈 Data Sources

- **Google Trends**: Real-time trending coffee keywords
- **Coffee Articles**: Professional coffee reviews and descriptions
- **RAG System**: TF-IDF vectorization for context retrieval

## 🔄 Workflow

1. **Trending Keywords** → Google Trends API scrapes current coffee trends
2. **Context Extraction** → NLP extracts coffee descriptors from articles
3. **RAG Retrieval** → Finds relevant context for each keyword
4. **Caption Generation** → Combines trending keywords + context + viral templates
5. **Output** → Catchy, engaging coffee captions ready for social media

## 💡 Tips for Best Results

- Run `GetCoffeTrend.py` regularly to get fresh trending keywords
- Add more coffee articles to `coffee_articles.csv` for richer context
- Experiment with different caption styles for variety
- Use the CLI for interactive caption generation

## 🎯 Perfect For

- Social media managers
- Coffee brands and cafes
- Content creators
- Coffee influencers
- Marketing campaigns

---

**Generated captions are ready-to-use for Instagram, LinkedIn, Twitter, and other social platforms!** ☕✨
