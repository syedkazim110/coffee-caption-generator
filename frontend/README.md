# ☕ Coffee Caption Generator - Frontend

This folder contains all the frontend components of the Coffee Caption Generator platform.

## 📁 Structure Overview

### Main Application Pages

#### **Main Caption Generator**
- **`index.html`** (18KB) - Main application interface
- **`styles.css`** (19KB) - Main application styles
- **`script.js`** (29KB) - Main application JavaScript logic

**Features:**
- Real-time caption generation with keyword input
- Platform selection (Instagram, Facebook, LinkedIn, Twitter)
- Brand selection dropdown
- AI model selection
- Scenario-based content generation
- Image generation and regeneration
- Context snippets display
- Copy to clipboard functionality
- Social media publishing integration

#### **Brand Onboarding**
- **`brand_onboarding.html`** (15KB) - Multi-step brand creation wizard
- **`brand_onboarding.css`** (8KB) - Brand onboarding styles
- **`brand_onboarding.js`** (19KB) - Brand onboarding logic

**Features:**
- 8-step wizard for comprehensive brand setup:
  1. Basic Information
  2. Brand Voice (AI-assisted adjectives)
  3. Tone Variations (AI-generated matrix)
  4. Lexicon Rules (AI suggestions)
  5. Content Guardrails
  6. Platform Strategy
  7. RAG Content Sources
  8. Social Media OAuth
- LLM-powered suggestions for brand voice
- Real-time validation
- Progress tracking
- Social media account connection

#### **Brand Management**
- **`brand_list.html`** (3.6KB) - Brand list and management interface
- **`brand_list.css`** (6KB) - Brand list styles
- **`brand_list.js`** (6KB) - Brand list logic

**Features:**
- View all brands
- Filter active/inactive brands
- Edit brand profiles
- Set active brand
- Delete brands
- Quick brand switching
- Brand statistics display

#### **AI Model Settings**
- **`ai_model_settings.html`** (4.6KB) - AI model configuration interface
- **`ai_model_settings.css`** (11KB) - AI settings styles
- **`ai_model_settings.js`** (21KB) - AI settings logic

**Features:**
- View all available AI models across providers
- Configure API keys for different providers
- Test model connectivity
- Set global default model
- Set brand-specific preferred models
- View model capabilities and pricing
- Provider summary (Ollama, OpenAI, Claude, Gemini)
- Real-time model status indicators

### Assets
- **`d8f4e234-309b-4e9f-b135-be8e1b4e5661.jpg`** (60KB) - Sample/placeholder image

## 🎨 Design System

### Color Scheme
```css
/* Main colors used throughout the app */
--primary: #8B4513 (Coffee Brown)
--secondary: #D4A574 (Light Coffee)
--accent: #6F4E37 (Dark Coffee)
--success: #4CAF50
--warning: #FF9800
--error: #F44336
--background: #F5F5F5
--card: #FFFFFF
```

### Typography
- **Font Family**: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen
- **Headings**: Bold, various sizes
- **Body**: Regular, 16px base

### Components
- Cards with shadows
- Modern buttons with hover effects
- Form inputs with validation
- Progress bars
- Modals and overlays
- Toast notifications
- Loading spinners
- Badges and tags

## 🚀 Getting Started

### Prerequisites
No build process required! This is vanilla HTML, CSS, and JavaScript.

### Development

#### Option 1: Docker (Recommended)
```bash
# Full-stack (frontend + backend)
cd ../backend/
docker-compose -f docker-compose.full-stack.yml up --build
# Visit: http://localhost:3000

# Frontend-only (backend elsewhere)
cd frontend/
docker-compose up --build
# Visit: http://localhost:3000
```

#### Option 2: Backend API Server
```bash
cd ../backend
python api.py
# Frontend served at: http://localhost:8000
```

#### Option 3: Static File Server
```bash
python -m http.server 8080
# Visit: http://localhost:8080
```

#### Option 4: VS Code Live Server
```bash
# Right-click index.html -> Open with Live Server
```

### Production

#### Option 1: Docker (Full-Stack)
```bash
cd ../backend/
docker-compose -f docker-compose.full-stack.yml up --build -d
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

#### Option 2: Docker (External Database)
```bash
cd ../backend/
docker-compose --env-file .env.external -f docker-compose.external-db.yml up --build -d
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

#### Option 3: Backend API Server
```bash
# The backend API server serves frontend files
# Files are served via FastAPI's FileResponse endpoints
python api.py
```

**See:** `../DOCKER_DEPLOYMENT.md` for complete deployment options.

## 📱 Pages & Features

### 1. Main Application (`index.html`)

**Layout:**
- Header with navigation and brand selector
- Control panel with:
  - Keyword input
  - Platform selector
  - Brand selector
  - AI model selector
  - Scenario dropdown
  - Generate button
- Output section with:
  - Generated caption with copy button
  - Hashtags display
  - Full caption preview
  - Generated image with regenerate option
  - Context snippets (collapsible)
  - Image prompt display
- Publishing section with platform checkboxes
- Statistics display

**Key Functions (script.js):**
- `generatePost()` - Generate complete post with caption and image
- `regenerateImage()` - Regenerate only the image
- `copyToClipboard()` - Copy text to clipboard
- `loadBrands()` - Fetch and populate brand dropdown
- `loadAIModels()` - Fetch available AI models
- `publishToSocialMedia()` - Publish to selected platforms
- `checkSocialConnections()` - Check OAuth connection status

### 2. Brand Onboarding (`brand_onboarding.html`)

**8-Step Wizard:**
1. **Basic Info**: Name, type, product, industry, audience
2. **Voice**: Core adjectives (with AI suggestions)
3. **Tones**: Scenario-based tone matrix (AI-generated)
4. **Lexicon**: Always use / never use words (AI suggestions)
5. **Guardrails**: Inappropriate topics, disclaimers, fact-check level
6. **Strategy**: Content mix ratios, platform-specific rules
7. **RAG Sources**: Custom URLs, RSS feeds, documents
8. **Social**: OAuth connections for publishing

**Key Functions (brand_onboarding.js):**
- `nextStep()` / `prevStep()` - Navigate wizard
- `suggestVoiceAdjectives()` - Get AI suggestions for voice
- `generateToneMatrix()` - Generate tone variations table
- `suggestLexicon()` - Get lexicon suggestions
- `submitBrand()` - Create brand profile
- `validateStep()` - Validate current step

### 3. Brand Management (`brand_list.html`)

**Features:**
- Searchable brand list
- Status indicators (active/inactive)
- Quick actions (edit, activate, delete)
- Brand statistics
- Bulk operations

**Key Functions (brand_list.js):**
- `loadBrands()` - Fetch all brands
- `filterBrands()` - Filter by search term
- `activateBrand()` - Set brand as active
- `editBrand()` - Navigate to edit page
- `deleteBrand()` - Delete with confirmation

### 4. AI Model Settings (`ai_model_settings.html`)

**Layout:**
- Provider tabs (Ollama, OpenAI, Anthropic, Google)
- Model cards with:
  - Model name and description
  - Capabilities badges
  - Status indicator
  - Configuration button
  - Test button
- Global settings panel
- API key management modals

**Key Functions (ai_model_settings.js):**
- `loadAIModels()` - Fetch all models and their status
- `configureModel()` - Set up API key for model
- `testModel()` - Test model connectivity
- `setDefaultModel()` - Set global default
- `showProvider()` - Switch between provider tabs

## 🔌 API Integration

All pages interact with the backend API at `http://localhost:8000`

### Main Endpoints Used

**Caption Generation:**
```javascript
POST /generate-post
Body: { keyword, brand_id, platform, scenario, model_id }
```

**Brand Management:**
```javascript
GET  /api/brands/list
POST /api/brands/create
GET  /api/brands/{brand_id}
PUT  /api/brands/{brand_id}
DELETE /api/brands/{brand_id}
```

**AI Models:**
```javascript
GET  /api/ai-models/list
POST /api/ai-models/{model_id}/configure
POST /api/ai-models/{model_id}/test
POST /api/ai-models/default
```

**Social Media:**
```javascript
POST /api/social/connect/{platform}
GET  /api/social/status
POST /api/social/publish
```

## 🎯 User Flow

1. **First Time Setup:**
   - Visit brand onboarding (`/brand_onboarding.html`)
   - Complete 8-step wizard
   - Connect social media accounts (optional)
   - Configure AI models (optional)

2. **Daily Usage:**
   - Select brand from dropdown
   - Choose platform
   - Enter keyword (optional, uses trending if empty)
   - Select scenario (optional)
   - Generate post
   - Review and edit caption
   - Regenerate image if needed
   - Publish to social media

3. **Brand Management:**
   - Switch between brands via dropdown
   - Edit brand profiles in brand list
   - View brand statistics
   - Manage multiple brands

4. **Model Configuration:**
   - Visit AI settings page
   - Configure API keys for premium models
   - Test model connectivity
   - Set preferred models per brand

## 🎨 Styling Guidelines

### CSS Organization
Each page has its own CSS file with:
- Reset/normalize
- Layout styles
- Component styles
- Responsive breakpoints
- Animations and transitions

### Responsive Design
- Mobile-first approach
- Breakpoints:
  - Mobile: < 768px
  - Tablet: 768px - 1024px
  - Desktop: > 1024px

### Accessibility
- Semantic HTML
- ARIA labels
- Keyboard navigation
- Color contrast compliance
- Screen reader friendly

## 🔧 Customization

### Adding a New Page
1. Create HTML file in frontend/
2. Create corresponding CSS and JS files
3. Add route in `api.py`:
```python
@app.get("/your-page.html")
async def get_your_page():
    return FileResponse("your-page.html")
```

### Modifying Existing Pages
1. Edit HTML structure
2. Update CSS styles
3. Modify JavaScript logic
4. Test with backend API

### Adding New Features
1. Update UI in HTML/CSS
2. Add JavaScript handlers
3. Create/modify backend endpoints if needed
4. Update API integration code

## 📱 Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## 🐛 Common Issues

### API Connection
```javascript
// Check if backend is running
fetch('http://localhost:8000/health')
  .then(res => res.json())
  .then(data => console.log('Backend status:', data));
```

### CORS Issues
- Backend has CORS middleware configured
- Allows all origins in development
- Update in production

### Loading Issues
- Ensure all assets are in frontend/
- Check browser console for errors
- Verify API endpoint URLs

## 📚 Additional Resources

- **Main Project README**: `../README.md` - Overall documentation
- **Backend API**: `../backend/README.md` - Backend documentation
- **Docker Deployment**: `../DOCKER_DEPLOYMENT.md` - All deployment options ⭐
- **External Database**: `../backend/EXTERNAL_DATABASE.md` - Production setup
- **Quick Setup**: `../EXTERNAL_DB_SETUP_SUMMARY.md` - 5-step guide
- **Command Reference**: `../DOCKER_COMMANDS_CHEATSHEET.md` - Docker commands
- **API Docs**: http://localhost:8000/docs - Interactive API documentation
- **Design System**: Check individual CSS files for components

## 🐳 Docker Deployment

This frontend can be deployed in multiple ways:

| Deployment | Use Case | Command | Access |
|------------|----------|---------|--------|
| **Full-Stack** | Development (all services) | `cd ../backend && docker-compose -f docker-compose.full-stack.yml up` | http://localhost:3000 |
| **External DB** | Production (AWS RDS/Azure/GCP) | `cd ../backend && docker-compose --env-file .env.external -f docker-compose.external-db.yml up` | http://localhost:3000 |
| **Frontend-Only** | Frontend dev (backend elsewhere) | `cd frontend && docker-compose up` | http://localhost:3000 |

**The frontend is served by Nginx in all Docker deployments with reverse proxy to backend API.**

## 🎨 Component Library

### Buttons
```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-success">Success</button>
```

### Cards
```html
<div class="card">
  <div class="card-header">Title</div>
  <div class="card-body">Content</div>
</div>
```

### Forms
```html
<div class="form-group">
  <label>Label</label>
  <input type="text" class="form-control">
</div>
```

### Modals
```html
<div class="modal" id="myModal">
  <div class="modal-content">
    <h2>Modal Title</h2>
    <p>Modal content</p>
  </div>
</div>
```

---

**For development questions, refer to the main project documentation or backend README.**

