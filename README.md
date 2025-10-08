# ☕ Catchy Coffee Caption Generator

A RAG-based system that generates viral-style coffee captions using trending Google Trends keywords and rich coffee context from articles.

## 🎯 Features

- **RAG-Powered**: Uses Retrieval-Augmented Generation to create contextually rich captions
- **Trending Keywords**: Leverages Google Trends data for current coffee topics
- **Multiple Styles**: 6 different viral caption styles (POV, relatable, trending, etc.)
- **Coffee Context**: Extracts flavor profiles and descriptions from coffee articles
- **Easy CLI**: Simple command-line interface for generating captions

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

2. **Start the application:**
   ```bash
   docker compose up --build
   ```

3. **Access the application:**
   - Web Interface: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

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

## 🐳 Docker Setup

The application is fully dockerized for easy deployment. The Docker setup includes:

- **PostgreSQL Database**: Persistent data storage with automatic initialization
- **Ollama LLM Service**: Local AI model for caption generation (phi3:mini)
- **FastAPI Web Application**: Python backend with hot-reload for development
- **Networking**: Internal Docker network for secure service communication
- **Health Checks**: Automatic service health monitoring

### Quick Start with Docker

**1. Start all services:**
```bash
docker compose up --build -d
```

**2. Setup Ollama model (first time only):**
```bash
./setup-ollama.sh
```

This downloads the phi3:mini model (~2GB). The model is cached and only needs to be downloaded once.

**3. Access the application:**
- Web Interface: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Commands

**Start services:**
```bash
docker compose up -d
```

**View logs:**
```bash
docker compose logs -f

# View specific service logs
docker compose logs -f web
docker compose logs -f ollama
docker compose logs -f postgres
```

**Stop services:**
```bash
docker compose down
```

**Rebuild after changes:**
```bash
docker compose up --build
```

**Access database:**
```bash
docker compose exec postgres psql -U postgres -d reddit_db
```

**Check Ollama models:**
```bash
docker compose exec ollama ollama list
```

**Pull different Ollama model:**
```bash
docker compose exec ollama ollama pull llama2
```

### Ports
- **Web Application**: http://localhost:8000
- **PostgreSQL**: localhost:5434
- **Ollama API**: localhost:11434

### GPU Support (Optional)

For faster LLM generation with NVIDIA GPU:

1. Install [nvidia-docker](https://github.com/NVIDIA/nvidia-docker)
2. Uncomment the GPU section in `docker-compose.yml` under the `ollama` service
3. Restart services: `docker compose up -d`

### Available Ollama Models

Default: `phi3:mini` (2GB, fast, good quality)

Other options:
- `llama2` (3.8GB, higher quality)
- `mistral` (4.1GB, excellent performance)
- `codellama` (3.8GB, code-focused)
- `gemma:2b` (1.4GB, fastest, lower quality)

To change model, update `OLLAMA_MODEL` in `.env` file.

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: ~5-10GB (includes models and data)
- **GPU**: Optional (NVIDIA GPU with nvidia-docker for acceleration)

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
