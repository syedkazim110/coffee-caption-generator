# 📁 Coffee Caption Generator - Folder Structure

This document explains the project organization after segregating frontend and backend components.

## 🎯 Overview

The project has been organized into dedicated frontend and backend folders while maintaining all original files in the root directory. This structure allows for:
- Clear separation of concerns
- Easier development and deployment
- Better code organization
- Simplified maintenance

## 📂 Folder Structure

```
coffee-caption-generator/
│
├── 📁 backend/              # Backend Components (Copies)
│   ├── *.py                 # All Python files
│   ├── *.sql                # Database schemas
│   ├── *.json               # Config and data files
│   ├── *.csv                # Data files
│   ├── ai_providers/        # AI provider implementations
│   ├── embeddings_cache/    # Cached embeddings
│   ├── Dockerfile           # Backend container
│   ├── requirements.txt     # Python dependencies
│   └── README.md           # Backend documentation
│
├── 📁 frontend/             # Frontend Components (Copies)
│   ├── index.html          # Main application
│   ├── script.js           # Main app logic
│   ├── styles.css          # Main app styles
│   ├── brand_onboarding.*  # Brand creation wizard
│   ├── brand_list.*        # Brand management
│   ├── ai_model_settings.* # AI configuration
│   ├── *.jpg               # Images
│   └── README.md          # Frontend documentation
│
├── 📁 social-oauth-service/ # OAuth Microservice
│   └── [OAuth service files]
│
├── 📁 archive/              # Archived data
│   └── [Old data files]
│
├── 📁 embeddings_cache/     # Original embeddings cache
│
├── [All original files]     # Original project files (unchanged)
│
├── README.md               # Main project documentation
├── DOCKER_SETUP.md         # Docker setup guide
├── FOLDER_STRUCTURE.md     # This file
├── docker-compose.yml      # Container orchestration
└── requirements.txt        # Python dependencies
```

## 📋 File Categorization

### Backend Files (in `backend/`)

**Core API & Services (9 files):**
- `api.py` - FastAPI application (main entry point)
- `llm_rag_caption_generator.py` - RAG + LLM engine
- `brand_manager.py` - Brand management
- `platform_strategies.py` - Platform rules
- `ai_service.py` - Multi-provider AI management
- `db_helper.py` - Database utilities
- `caption_generator_cli.py` - CLI tool
- `rag_caption_generator.py` - Original RAG generator
- `coffee_context_extractor.py` - Context extraction

**Data Collection (6 files):**
- `GetCoffeTrend.py` - Google Trends scraper
- `coffee_blog_scraper.py` - Blog scraper
- `blogs_articles.py` - Blog management
- `Reddit.py` - Reddit scraper
- `twitter.py` - Twitter scraper
- `simple_hashtag_scraper.py` - Hashtag scraper

**Database (7 files):**
- `init.sql` - Core schema
- `init_brand_schema.sql` - Brand schema
- `migration_schema.sql` - Extended schema
- `add_api_key_management.sql` - API keys
- `add_preferred_llm_model.sql` - Model preferences
- `clean_database.sql` - Cleanup scripts
- `init_database.py` - DB initialization

**Utilities (8 files):**
- `migrate_data_to_postgres.py` - Data migration
- `migrate_trending_keywords.py` - Keyword migration
- `backup_database.py` - Backup tools
- `view_database.py` - DB inspection
- `clean_csv_files.py` - CSV cleaning
- `validate_data_quality.py` - Validation
- `run_data_cleaning.py` - Cleaning pipeline
- `archive_old_files.py` - Archiving

**Testing (10+ files):**
- `test_ai_service.py`
- `test_db.py`
- `test_brand_voice_logging.py`
- `test_brand_image_generation.py`
- `test_hashtag_loading.py`
- `test_keyword_loading.py`
- `test_scenario_enforcement.py`
- `test_attribution_removal.py`
- `test_transaction_fix.py`
- `test_truncation_fix.py`
- And more...

**Data Files (15+ files):**
- `coffee_articles.csv` / `.json`
- `coffee_context.json`
- `coffee_hashtag_knowledge_base.json`
- `coffee_hashtags_trending.json`
- `trending_coffee_keywords.json`
- `hashtag_knowledge_base.json`
- `worldwide_coffee_habits.csv`
- `llm_rag_captions.json`
- `rag_generated_captions.json`
- `complete_social_media_posts.json`
- Various test results JSON files

**Docker & Config (6 files):**
- `Dockerfile`
- `Dockerfile.ollama`
- `docker-compose.yml`
- `setup-ollama.sh`
- `requirements.txt`
- `ai_model_config.json`

**AI Providers Module:**
- `ai_providers/__init__.py`
- `ai_providers/base_provider.py`
- `ai_providers/ollama_provider.py`
- `ai_providers/openai_provider.py`
- `ai_providers/anthropic_provider.py`
- `ai_providers/gemini_provider.py`

### Frontend Files (in `frontend/`)

**Main Application (3 files):**
- `index.html` - Main UI (18KB)
- `script.js` - Main logic (29KB)
- `styles.css` - Main styles (19KB)

**Brand Onboarding (3 files):**
- `brand_onboarding.html` - Wizard UI (15KB)
- `brand_onboarding.js` - Wizard logic (19KB)
- `brand_onboarding.css` - Wizard styles (8KB)

**Brand Management (3 files):**
- `brand_list.html` - List UI (3.6KB)
- `brand_list.js` - List logic (6KB)
- `brand_list.css` - List styles (6KB)

**AI Settings (3 files):**
- `ai_model_settings.html` - Settings UI (4.6KB)
- `ai_model_settings.js` - Settings logic (21KB)
- `ai_model_settings.css` - Settings styles (11KB)

**Assets (1 file):**
- `d8f4e234-309b-4e9f-b135-be8e1b4e5661.jpg` - Sample image

## 🚀 Usage Guide

### For Development

**Backend Development:**
```bash
cd backend/
pip install -r requirements.txt
python api.py
```

**Frontend Development:**
```bash
cd frontend/
# Use any static server or open index.html directly
python -m http.server 8080
```

**Full Stack Development:**
```bash
# From project root
docker-compose up --build
```

### For Deployment

**Backend Only:**
```bash
cd backend/
docker build -t coffee-backend .
docker run -p 8000:8000 coffee-backend
```

**Frontend Only:**
```bash
cd frontend/
# Deploy to static hosting (Netlify, Vercel, S3, etc.)
```

**Full Application:**
```bash
# From project root
docker-compose up -d
```

## 📚 Documentation

- **Main Project**: `/README.md` - Overall documentation
- **Backend**: `/backend/README.md` - Backend specifics
- **Frontend**: `/frontend/README.md` - Frontend specifics
- **Docker**: `/DOCKER_SETUP.md` - Docker deployment
- **This File**: `/FOLDER_STRUCTURE.md` - Folder organization

## 🔄 Working with Both Copies

### Why Keep Duplicates?

1. **Original Structure**: Maintains backward compatibility
2. **Organized Development**: Clear separation for developers
3. **Flexible Deployment**: Can deploy frontend/backend separately
4. **Easy Navigation**: Developers can focus on their domain

### Which Files to Edit?

**For Active Development:**
- Edit files in `backend/` or `frontend/` folders
- These are your working copies

**Syncing Changes (Optional):**
If you want to keep root files in sync:
```bash
# Copy backend changes to root
cp backend/*.py .
cp backend/*.sql .

# Copy frontend changes to root
cp frontend/*.html .
cp frontend/*.css .
cp frontend/*.js .
```

**Recommendation:**
For simplicity, you can:
1. Work only in `backend/` and `frontend/` folders
2. Update root files periodically if needed
3. Or, consider moving entirely to the segregated structure

## 🎯 Next Steps

### Option 1: Continue with Dual Structure
- Keep both root files and segregated folders
- Edit in segregated folders for development
- Sync to root occasionally

### Option 2: Move to Segregated Structure
- Update `api.py` to serve frontend from `frontend/` folder
- Update `Dockerfile` to use new structure
- Remove duplicate files from root
- Update documentation

### Option 3: Git Submodules (Advanced)
- Make `frontend/` a separate Git repository
- Make `backend/` a separate Git repository
- Use main repo to orchestrate both

## 📝 Notes

- All files in `backend/` and `frontend/` are **copies** of originals
- Original files in root remain **unchanged**
- Both structures work with current `docker-compose.yml`
- The FastAPI app still serves frontend files from root by default
- No breaking changes to existing functionality

## 🔧 Maintenance

### Adding New Backend Files
```bash
# Add to both locations
touch new_file.py
cp new_file.py backend/
```

### Adding New Frontend Files
```bash
# Add to both locations
touch new_file.html
cp new_file.html frontend/
```

### Cleaning Up (Future)
When ready to use only segregated structure:
1. Update `api.py` paths to `frontend/`
2. Update Docker volumes
3. Remove duplicate files from root
4. Update all documentation

---

**This structure provides flexibility for your development workflow while maintaining the original project structure intact.**

