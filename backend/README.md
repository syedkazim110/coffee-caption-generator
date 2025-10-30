# ☕ Coffee Caption Generator - Backend

This folder contains all the backend components of the Coffee Caption Generator platform.

## 📁 Structure Overview

### Core API & Services
- **`api.py`** (44KB) - Main FastAPI application with 40+ REST endpoints
- **`llm_rag_caption_generator.py`** (2450 lines) - RAG + LLM caption generation engine
- **`brand_manager.py`** (25KB) - Brand profile CRUD operations and LLM suggestions
- **`platform_strategies.py`** - Platform-specific content rules (Instagram, Facebook, etc.)
- **`ai_service.py`** (22KB) - Multi-provider AI model management (Ollama, OpenAI, Claude, Gemini)

### AI Providers Module
- **`ai_providers/`** - Provider implementations for different AI services
  - `base_provider.py` - Abstract base class for AI providers
  - `ollama_provider.py` - Local Ollama LLM integration
  - `openai_provider.py` - OpenAI GPT models
  - `anthropic_provider.py` - Claude models
  - `gemini_provider.py` - Google Gemini models

### Data Collection & Scraping
- **`GetCoffeTrend.py`** - Google Trends keyword scraper for coffee topics
- **`coffee_blog_scraper.py`** - Scrapes coffee blogs for RAG content
- **`blogs_articles.py`** (41KB) - Blog article management
- **`Reddit.py`** - Reddit data scraper for coffee discussions
- **`twitter.py`** - Twitter/X data scraper
- **`simple_hashtag_scraper.py`** - Hashtag trend scraper

### Database
- **`init.sql`** - Core database schema (14 tables)
- **`init_brand_schema.sql`** - Brand profile schema
- **`migration_schema.sql`** - Extended schema with RAG and analytics tables
- **`add_api_key_management.sql`** - API credentials management
- **`add_preferred_llm_model.sql`** - Brand-level AI model preferences
- **`clean_database.sql`** - Database cleanup scripts

### Database Helper Scripts
- **`init_database.py`** - Database initialization
- **`migrate_data_to_postgres.py`** - Data migration utilities
- **`migrate_trending_keywords.py`** - Migrate trending keywords to DB
- **`db_helper.py`** - Database connection helpers
- **`backup_database.py`** - Database backup utilities
- **`view_database.py`** - Database inspection tools

### Utilities & Tools
- **`caption_generator_cli.py`** - Command-line interface for caption generation
- **`coffee_context_extractor.py`** - Extracts coffee terminology from articles
- **`rag_caption_generator.py`** - Original RAG-based generator
- **`get_image_prompts.py`** - Image prompt generation utilities
- **`clean_csv_files.py`** - CSV data cleaning
- **`validate_data_quality.py`** - Data quality validation
- **`run_data_cleaning.py`** - Data cleaning pipeline
- **`archive_old_files.py`** - File archiving utilities
- **`show_brand_voice_data.py`** - Brand voice data visualization

### Testing Scripts
- **`test_*.py`** - Various test files for different components:
  - `test_ai_service.py` - AI service tests
  - `test_db.py` - Database tests
  - `test_brand_voice_logging.py` - Brand voice tests
  - `test_brand_image_generation.py` - Image generation tests
  - `test_hashtag_loading.py` - Hashtag loading tests
  - `test_keyword_loading.py` - Keyword loading tests
  - And more...

### Data Files
- **`coffee_articles.csv`** - Coffee articles for RAG (77KB)
- **`coffee_articles.json`** - JSON version of articles (80KB)
- **`coffee_context.json`** - Extracted coffee context
- **`coffee_hashtag_knowledge_base.json`** (98KB) - Hashtag database
- **`coffee_hashtags_trending.json`** - Trending hashtags
- **`trending_coffee_keywords.json`** - Trending keywords from Google Trends
- **`hashtag_knowledge_base.json`** - Extended hashtag knowledge
- **`worldwide_coffee_habits.csv`** - Global coffee consumption data
- **`ai_model_config.json`** - AI model configurations

### Generated Content Cache
- **`llm_rag_captions.json`** - Generated captions cache
- **`rag_generated_captions.json`** - RAG-generated captions
- **`complete_social_media_posts.json`** - Complete posts with images
- **`embeddings_cache/`** - Cached embeddings for RAG performance

### Docker & Deployment
- **`Dockerfile.backend`** - Backend application Docker image
- **`docker-compose.yml`** - Backend-only deployment (with local databases)
- **`docker-compose.full-stack.yml`** - Complete application (frontend + backend + databases)
- **`docker-compose.external-db.yml`** - Production deployment (external database) ⭐
- **`setup-ollama.sh`** - Ollama setup script
- **`requirements.txt`** - Python dependencies
- **`EXTERNAL_DATABASE.md`** - External database setup guide
- **`ENV_EXTERNAL_TEMPLATE.txt`** - Environment template for external DB

### Configuration Files
- **`ai_model_config.json`** - AI model configurations
- **Various test results JSON files** - Test outputs and results

## 🚀 Getting Started

### Prerequisites
```bash
# Python 3.9+
pip install -r requirements.txt

# PostgreSQL (or use Docker)
# Ollama (optional, for local LLM)
```

### Database Setup

**Option 1: Local Database (Docker)**
```bash
# Full-stack with local PostgreSQL
docker-compose -f docker-compose.full-stack.yml up -d postgres

# Or backend-only
docker-compose up -d postgres
```

**Option 2: External Database (Production)**
```bash
# See EXTERNAL_DATABASE.md for complete setup
# Initialize external database with SQL files
psql -h your-db-host.rds.amazonaws.com -U postgres -d reddit_db -f init.sql
psql -h your-db-host.rds.amazonaws.com -U postgres -d reddit_db -f init_brand_schema.sql
# ... (see EXTERNAL_DATABASE.md)
```

**Option 3: Manual Setup**
```bash
# Initialize database
python init_database.py
```

### Run the API

**Option 1: Full-Stack (Development)**
```bash
cd backend/
docker-compose -f docker-compose.full-stack.yml up --build
# Access: http://localhost:3000 (frontend) and http://localhost:8000 (backend)
```

**Option 2: External Database (Production)**
```bash
cd backend/
# Create .env.external with database credentials
cat ENV_EXTERNAL_TEMPLATE.txt > .env.external
# Edit .env.external, then:
docker-compose --env-file .env.external -f docker-compose.external-db.yml up --build
```

**Option 3: Backend-Only (Development)**
```bash
docker-compose up --build
# Access: http://localhost:8000
```

**Option 4: Manual (No Docker)**
```bash
# With uvicorn
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Or directly
python api.py
```

### API Endpoints
- **Main API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📊 Key Technologies

- **Framework**: FastAPI
- **Database**: PostgreSQL 15
- **AI/LLM**: 
  - Ollama (local, phi3:mini)
  - OpenAI GPT-4/3.5
  - Anthropic Claude
  - Google Gemini
- **RAG**: TF-IDF + Sentence Transformers
- **Data Processing**: pandas, numpy, scikit-learn
- **Web Scraping**: BeautifulSoup, requests
- **Social Media**: praw (Reddit), tweepy (Twitter)

## 🗄️ Database Schema

14 tables organized into:
- **Brand Management**: brand_profiles
- **Content Sources**: coffee_articles, blog_articles, reddit_data, twitter_data
- **Knowledge Bases**: hashtag_knowledge, trending_keywords, coffee_context
- **Generated Content**: generated_captions, social_media_posts, image_prompts
- **RAG**: rag_documents
- **AI Config**: ai_model_settings, api_credentials

## 📝 Environment Variables

### For Full-Stack or Backend-Only (Local Database)

Create `.env` file:
```env
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=reddit_db
DB_USER=postgres
DB_PASSWORD=postgres123

# AI Services (optional)
GEMINI_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Ollama (local LLM)
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=phi3:mini

# OAuth Service (for social media publishing)
OAUTH_SERVICE_URL=http://oauth-service:8001
OAUTH_SERVICE_API_KEY=dev-service-key
```

### For External Database (Production)

Create `.env.external` file (see `ENV_EXTERNAL_TEMPLATE.txt`):
```env
# External Database (REQUIRED)
DB_HOST=your-db.rds.amazonaws.com
DB_PORT=5432
DB_NAME=reddit_db
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_SSL_MODE=require

# Security (REQUIRED)
ENCRYPTION_KEY=your-32-byte-encryption-key
SECRET_KEY=your-secret-key
OAUTH_SERVICE_API_KEY=your-service-api-key

# AI Services (optional)
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Ollama
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=phi3:mini

# OAuth Service
OAUTH_SERVICE_URL=http://oauth-service:8001
```

**See:** `EXTERNAL_DATABASE.md` for complete external database setup.

## 🔧 Development

### Run Tests
```bash
# Run all tests
python -m pytest

# Run specific test
python test_ai_service.py
python test_db.py
```

### Data Collection
```bash
# Scrape Google Trends
python GetCoffeTrend.py

# Scrape coffee blogs
python coffee_blog_scraper.py

# Extract context
python coffee_context_extractor.py
```

### CLI Tools
```bash
# Interactive caption generator
python caption_generator_cli.py

# View database contents
python view_database.py

# Show brand voice data
python show_brand_voice_data.py
```

## 📚 API Documentation

Full API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints
- `POST /generate-post` - Generate complete social media post
- `POST /regenerate-image` - Regenerate image for existing post
- `GET /api/brands/list` - List all brands
- `POST /api/brands/create` - Create new brand
- `GET /api/ai-models/list` - List available AI models
- `POST /api/social/publish` - Publish to social media

## 🔐 Security Notes

- API keys are stored encrypted in the database
- OAuth tokens are managed by separate OAuth service
- Always use environment variables for sensitive data
- Never commit `.env` files to version control

## 📖 Additional Documentation

- **Main Project README**: `../README.md` - Overall documentation
- **Docker Deployment Guide**: `../DOCKER_DEPLOYMENT.md` - All deployment options
- **External Database Setup**: `EXTERNAL_DATABASE.md` - AWS RDS, Azure, GCP setup ⭐
- **Quick Setup Guide**: `../EXTERNAL_DB_SETUP_SUMMARY.md` - 5-step quick start
- **Command Cheat Sheet**: `../DOCKER_COMMANDS_CHEATSHEET.md` - All Docker commands
- **Deployment Summary**: `../DOCKER_SEPARATION_SUMMARY.txt` - Quick reference
- **Frontend Documentation**: `../frontend/README.md` - Frontend details
- **Inline Documentation**: Each major module has detailed comments

## 🚀 Deployment Options Summary

| Option | Use Case | Database | Command |
|--------|----------|----------|---------|
| **Full-Stack** | Development | Local PostgreSQL | `docker-compose -f docker-compose.full-stack.yml up` |
| **External DB** | Production | AWS RDS/Azure/GCP | `docker-compose --env-file .env.external -f docker-compose.external-db.yml up` |
| **Backend-Only** | Backend dev | Local PostgreSQL | `docker-compose up` |
| **Frontend-Only** | Frontend dev | External backend | See `../frontend/README.md` |

**Choose the right option for your needs and follow the corresponding guide!**

