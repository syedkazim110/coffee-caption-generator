# 🐳 Docker Deployment Guide - Coffee Caption Generator

This guide explains how to deploy the Coffee Caption Generator using the separated Docker configurations for frontend and backend.

## 📁 Docker Files Overview

### Backend Files
```
backend/
├── Dockerfile.backend          # Backend container image
├── docker-compose.yml          # Backend-only deployment
└── .env.example               # Backend environment template
```

### Frontend Files
```
frontend/
├── Dockerfile.frontend         # Frontend nginx container
├── nginx.conf                 # Nginx configuration
├── docker-compose.yml         # Frontend-only deployment
└── .env.example              # Frontend environment template
```

### Full Stack
```
root/
├── docker-compose.full-stack.yml  # Complete application
└── .env.example                  # Full-stack environment template
```

---

## 🚀 Deployment Options

### Option 1: Full-Stack Deployment (Recommended for Development)

**Best for:** Local development, testing

Deploy both frontend and backend together:

```bash
# From backend folder
cd backend/
docker-compose -f docker-compose.full-stack.yml up --build

# Or in detached mode
docker-compose -f docker-compose.full-stack.yml up --build -d
```

**What it includes:**
- PostgreSQL (main database)
- Ollama (local LLM)
- OAuth Service
- OAuth Database
- Backend API
- Frontend (nginx)

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### Option 2: External Database Deployment (Recommended for Production)

**Best for:** Production with AWS RDS, Azure Database, Google Cloud SQL

Deploy backend and frontend with external managed database:

```bash
# Navigate to backend folder
cd backend/

# Create environment file with database credentials
cp .env.external.example .env.external
# Edit .env.external with your database details

# Start services
docker-compose --env-file .env.external -f docker-compose.external-db.yml up --build

# Or in detached mode
docker-compose --env-file .env.external -f docker-compose.external-db.yml up --build -d
```

**What it includes:**
- Backend API
- Frontend (nginx)
- Ollama (local LLM)
- OAuth Service
- **No PostgreSQL containers** (uses your external database)

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Use Case:**
- Production deployments
- AWS RDS, Azure Database, Google Cloud SQL
- Scalable database infrastructure
- Enterprise database features

**See detailed setup:** `backend/EXTERNAL_DATABASE.md`

---

### Option 3: Backend-Only Deployment

**Best for:** Backend development, microservices

Deploy just the backend services:

```bash
# Navigate to backend folder
cd backend/

# Start backend services
docker-compose up --build

# Or in detached mode
docker-compose up --build -d
```

**What it includes:**
- PostgreSQL (main database)
- Ollama (local LLM)
- OAuth Service
- OAuth Database
- Backend API

**Access:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Ollama: http://localhost:11434

**Use Case:**
- When you want to run frontend separately (e.g., React dev server)
- Microservices architecture
- Backend development

---

### Option 4: Frontend-Only Deployment

**Best for:** Frontend development, CDN deployment

Deploy just the frontend:

```bash
# Navigate to frontend folder
cd frontend/

# Start frontend service
docker-compose up --build

# Or in detached mode
docker-compose up --build -d
```

**What it includes:**
- Nginx server with static files

**Access:**
- Frontend: http://localhost:3000

**Use Case:**
- When backend is deployed elsewhere
- Testing frontend changes
- CDN deployment preparation

**Note:** You need to configure BACKEND_URL to point to your backend API.

---

## ⚙️ Environment Configuration

### Backend Environment Variables

Create `backend/.env` from `backend/.env.example`:

```bash
cd backend/
cp .env.example .env
# Edit .env with your values
```

**Required Variables:**
```env
# Database
DB_PASSWORD=your_secure_password

# Security (change in production!)
ENCRYPTION_KEY=your-32-byte-encryption-key
SECRET_KEY=your-secret-key
OAUTH_SERVICE_API_KEY=your-service-key
```

**Optional Variables:**
```env
# AI Services
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# OAuth
INSTAGRAM_CLIENT_ID=your_id
INSTAGRAM_CLIENT_SECRET=your_secret
FACEBOOK_CLIENT_ID=your_id
FACEBOOK_CLIENT_SECRET=your_secret
```

### Frontend Environment Variables

Create `frontend/.env`:

```bash
cd frontend/
echo "FRONTEND_PORT=3000" > .env
echo "BACKEND_URL=http://backend:8000" >> .env
```

**For Production:**
```env
BACKEND_URL=https://api.yourdomain.com
```

### Full-Stack Environment Variables

For full-stack deployment, create `.env` in root:

```bash
cp .env.example .env
# Edit .env with your values
```

---

## 🔧 Common Commands

### Start Services

```bash
# Full stack (development)
cd backend && docker-compose -f docker-compose.full-stack.yml up -d

# External database (production)
cd backend && docker-compose --env-file .env.external -f docker-compose.external-db.yml up -d

# Backend only
cd backend && docker-compose up -d

# Frontend only
cd frontend && docker-compose up -d
```

### Stop Services

```bash
# Full stack
cd backend && docker-compose -f docker-compose.full-stack.yml down

# External database
cd backend && docker-compose -f docker-compose.external-db.yml down

# Backend only
cd backend && docker-compose down

# Frontend only
cd frontend && docker-compose down
```

### View Logs

```bash
# Full stack - all services
cd backend && docker-compose -f docker-compose.full-stack.yml logs -f

# Full stack - specific service
cd backend && docker-compose -f docker-compose.full-stack.yml logs -f backend
cd backend && docker-compose -f docker-compose.full-stack.yml logs -f frontend

# Backend only
cd backend && docker-compose logs -f

# Frontend only
cd frontend && docker-compose logs -f
```

### Rebuild Containers

```bash
# Full stack
cd backend && docker-compose -f docker-compose.full-stack.yml up --build --force-recreate

# Backend only
cd backend && docker-compose up --build --force-recreate

# Frontend only
cd frontend && docker-compose up --build --force-recreate
```

### Stop and Remove Everything

```bash
# Full stack (including volumes)
cd backend && docker-compose -f docker-compose.full-stack.yml down -v

# Backend only (including volumes)
cd backend && docker-compose down -v

# Frontend only
cd frontend && docker-compose down
```

---

## 📦 Database Management

### Access PostgreSQL (Main Database)

```bash
# Full stack
cd backend && docker-compose -f docker-compose.full-stack.yml exec postgres psql -U postgres -d reddit_db

# Backend only
cd backend && docker-compose exec postgres psql -U postgres -d reddit_db
```

### Backup Database

```bash
# Full stack
cd backend && docker-compose -f docker-compose.full-stack.yml exec postgres pg_dump -U postgres reddit_db > backup.sql

# Backend only
cd backend && docker-compose exec postgres pg_dump -U postgres reddit_db > backup.sql
```

### Restore Database

```bash
# Full stack
cd backend && cat backup.sql | docker-compose -f docker-compose.full-stack.yml exec -T postgres psql -U postgres reddit_db

# Backend only
cd backend && cat backup.sql | docker-compose exec -T postgres psql -U postgres reddit_db
```

---

## 🧪 Testing Deployments

### Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Get statistics
curl http://localhost:8000/statistics

# List brands
curl http://localhost:8000/api/brands/list
```

### Test Frontend

```bash
# Check nginx is serving
curl http://localhost:3000

# Should return HTML
curl -I http://localhost:3000
```

### Test Full Stack Integration

```bash
# Generate a post (requires backend + frontend)
curl -X POST http://localhost:8000/generate-post \
  -H "Content-Type: application/json" \
  -d '{"keyword": "cold brew"}'
```

---

## 🌐 Production Deployment

### Backend Production

1. **Use production .env:**
```env
DEBUG=false
DB_PASSWORD=strong_password
ENCRYPTION_KEY=secure-32-byte-key
SECRET_KEY=secure-secret-key
```

2. **Use external database:**
```env
DB_HOST=your-db-host.com
DB_PORT=5432
```

3. **Deploy with restart policy:**
```yaml
# Already configured in docker-compose files
restart: unless-stopped
```

4. **Use reverse proxy (nginx/traefik):**
```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

### Frontend Production

1. **Build optimized image:**
```bash
cd frontend
docker build -t coffee-frontend:prod -f Dockerfile.frontend .
```

2. **Configure backend URL:**
```nginx
# Update nginx.conf
location /api/ {
    proxy_pass https://api.yourdomain.com/api/;
}
```

3. **Deploy to CDN (optional):**
```bash
# Copy built files to CDN
docker cp coffee_frontend:/usr/share/nginx/html ./dist
# Upload ./dist to S3/CloudFlare/etc.
```

### Full-Stack Production

1. **Use docker-compose.full-stack.yml from backend/ folder**
2. **Configure production .env in backend/ folder**
3. **Use SSL certificates**
4. **Set up monitoring**

---

## 🔒 Security Checklist

- [ ] Change all default passwords
- [ ] Generate secure ENCRYPTION_KEY (32 bytes)
- [ ] Generate secure SECRET_KEY
- [ ] Change OAUTH_SERVICE_API_KEY
- [ ] Use HTTPS in production
- [ ] Restrict database access
- [ ] Keep Docker images updated
- [ ] Use secrets management (Docker Secrets/Vault)
- [ ] Enable firewall rules
- [ ] Regular backups

---

## 📊 Port Reference

| Service | Port | Access |
|---------|------|--------|
| Frontend | 3000 | http://localhost:3000 |
| Backend API | 8000 | http://localhost:8000 |
| OAuth Service | 8001 | http://localhost:8001 |
| PostgreSQL (main) | 5433 | localhost:5433 |
| PostgreSQL (OAuth) | 5435 | localhost:5435 |
| Ollama | 11434 | http://localhost:11434 |

**Note:** Ports can be customized via environment variables.

---

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check logs
cd backend && docker-compose -f docker-compose.full-stack.yml logs backend

# Common issues:
# - Database not ready: Wait for health check
# - Missing .env: Copy from .env.example
# - Port in use: Change API_PORT
```

### Frontend Won't Connect to Backend

```bash
# Check nginx.conf backend URL
cat frontend/nginx.conf | grep proxy_pass

# Check if backend is running
curl http://localhost:8000/health

# Check frontend logs
docker-compose logs frontend
```

### Database Connection Failed

```bash
# Check postgres is healthy
docker-compose ps

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U postgres -d reddit_db -c "SELECT 1"
```

### Ollama Model Not Loading

```bash
# Check ollama logs
docker-compose logs ollama

# Pull model manually
docker-compose exec ollama ollama pull phi3:mini

# List available models
docker-compose exec ollama ollama list
```

---

## 📚 Additional Resources

- **Backend README**: `backend/README.md`
- **Frontend README**: `frontend/README.md`
- **External Database Setup**: `backend/EXTERNAL_DATABASE.md` ⭐
- **Original Docker Setup**: `DOCKER_SETUP.md`
- **Project Structure**: `FOLDER_STRUCTURE.md`

---

## 🎯 Quick Start Summary

**Full-Stack (Development):**
```bash
cd backend
docker-compose -f docker-compose.full-stack.yml up --build
# Visit: http://localhost:3000
```

**External Database (Production):**
```bash
cd backend
cp .env.external.example .env.external
# Edit .env.external with your database details
docker-compose --env-file .env.external -f docker-compose.external-db.yml up --build
# Visit: http://localhost:3000
```

**Backend Only:**
```bash
cd backend && docker-compose up --build
# API: http://localhost:8000
```

**Frontend Only:**
```bash
cd frontend && docker-compose up --build
# Web: http://localhost:3000
```

**Stop All:**
```bash
cd backend && docker-compose -f docker-compose.full-stack.yml down
# or
cd backend && docker-compose -f docker-compose.external-db.yml down
```

---

**For detailed API documentation, visit: http://localhost:8000/docs**

