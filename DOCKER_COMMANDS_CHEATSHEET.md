# 🐳 Docker Commands Cheat Sheet

Quick reference for all Docker Compose deployment options in this project.

---

## 📋 Table of Contents

1. [Full-Stack (Development)](#full-stack-development)
2. [External Database (Production)](#external-database-production)
3. [Backend-Only](#backend-only)
4. [Frontend-Only](#frontend-only)
5. [Common Commands](#common-commands)
6. [Troubleshooting](#troubleshooting)

---

## 1️⃣ Full-Stack (Development)

**Location:** `backend/docker-compose.full-stack.yml`  
**Use Case:** Local development with all services

### Start
```bash
cd backend/
docker-compose -f docker-compose.full-stack.yml up --build
```

### Start (detached)
```bash
docker-compose -f docker-compose.full-stack.yml up --build -d
```

### View logs
```bash
docker-compose -f docker-compose.full-stack.yml logs -f
```

### Stop
```bash
docker-compose -f docker-compose.full-stack.yml down
```

### Stop and remove volumes
```bash
docker-compose -f docker-compose.full-stack.yml down -v
```

### Restart specific service
```bash
docker-compose -f docker-compose.full-stack.yml restart backend
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## 2️⃣ External Database (Production)

**Location:** `backend/docker-compose.external-db.yml`  
**Use Case:** Production with AWS RDS, Azure Database, etc.

### Setup (first time)
```bash
cd backend/

# Create environment file
cat ENV_EXTERNAL_TEMPLATE.txt > .env.external

# Edit with your database credentials
nano .env.external
```

### Start
```bash
docker-compose --env-file .env.external -f docker-compose.external-db.yml up --build
```

### Start (detached)
```bash
docker-compose --env-file .env.external -f docker-compose.external-db.yml up --build -d
```

### View logs
```bash
docker-compose -f docker-compose.external-db.yml logs -f
```

### View logs (specific service)
```bash
docker-compose -f docker-compose.external-db.yml logs -f backend
```

### Stop
```bash
docker-compose -f docker-compose.external-db.yml down
```

### Restart backend
```bash
docker-compose -f docker-compose.external-db.yml restart backend
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Docs: http://localhost:8000/docs

**See also:** `backend/EXTERNAL_DATABASE.md`

---

## 3️⃣ Backend-Only

**Location:** `backend/docker-compose.yml`  
**Use Case:** Backend development only

### Start
```bash
cd backend/
docker-compose up --build
```

### Start (detached)
```bash
docker-compose up --build -d
```

### View logs
```bash
docker-compose logs -f
```

### Stop
```bash
docker-compose down
```

### Stop and remove volumes
```bash
docker-compose down -v
```

**Access:**
- Backend: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## 4️⃣ Frontend-Only

**Location:** `frontend/docker-compose.yml`  
**Use Case:** Frontend development with backend elsewhere

### Start
```bash
cd frontend/
docker-compose up --build
```

### Start (detached)
```bash
docker-compose up --build -d
```

### View logs
```bash
docker-compose logs -f
```

### Stop
```bash
docker-compose down
```

**Access:**
- Frontend: http://localhost:3000

---

## 🔧 Common Commands

### View all running containers
```bash
docker ps
```

### View all containers (including stopped)
```bash
docker ps -a
```

### View Docker Compose services status
```bash
# Full-stack
cd backend && docker-compose -f docker-compose.full-stack.yml ps

# External DB
cd backend && docker-compose -f docker-compose.external-db.yml ps

# Backend only
cd backend && docker-compose ps

# Frontend only
cd frontend && docker-compose ps
```

### Execute command in container
```bash
# Full-stack
docker-compose -f docker-compose.full-stack.yml exec backend bash

# External DB
docker-compose -f docker-compose.external-db.yml exec backend bash

# Backend only
cd backend && docker-compose exec backend bash
```

### View container resource usage
```bash
docker stats
```

### Rebuild specific service
```bash
# Full-stack
docker-compose -f docker-compose.full-stack.yml up --build backend

# External DB
docker-compose -f docker-compose.external-db.yml up --build backend

# Backend only
docker-compose up --build backend
```

### Remove all stopped containers
```bash
docker container prune
```

### Remove all unused images
```bash
docker image prune -a
```

### Remove all unused volumes
```bash
docker volume prune
```

### Clean up everything (careful!)
```bash
docker system prune -a --volumes
```

---

## 🐛 Troubleshooting

### Check backend health
```bash
curl http://localhost:8000/health
```

### Check database connection (full-stack)
```bash
cd backend
docker-compose -f docker-compose.full-stack.yml exec postgres psql -U postgres -c '\l'
```

### Check database connection (external DB)
```bash
# From Docker host
psql -h your-db-host.rds.amazonaws.com -U postgres -d reddit_db -c '\dt'
```

### View PostgreSQL logs (full-stack)
```bash
cd backend
docker-compose -f docker-compose.full-stack.yml logs postgres
```

### View backend environment variables
```bash
# Full-stack
docker-compose -f docker-compose.full-stack.yml exec backend env | grep DB_

# External DB
docker-compose -f docker-compose.external-db.yml exec backend env | grep DB_
```

### Restart all services
```bash
# Full-stack
docker-compose -f docker-compose.full-stack.yml restart

# External DB
docker-compose -f docker-compose.external-db.yml restart
```

### Force recreate containers
```bash
# Full-stack
docker-compose -f docker-compose.full-stack.yml up --force-recreate --build

# External DB
docker-compose -f docker-compose.external-db.yml up --force-recreate --build
```

### View network information
```bash
docker network ls
docker network inspect coffee_network
```

### Check Ollama models
```bash
# Full-stack
docker-compose -f docker-compose.full-stack.yml exec ollama ollama list

# External DB
docker-compose -f docker-compose.external-db.yml exec ollama ollama list
```

### Access PostgreSQL shell (full-stack)
```bash
cd backend
docker-compose -f docker-compose.full-stack.yml exec postgres psql -U postgres -d reddit_db
```

### Backup database (full-stack)
```bash
cd backend
docker-compose -f docker-compose.full-stack.yml exec postgres pg_dump -U postgres reddit_db > backup.sql
```

### Restore database (full-stack)
```bash
cd backend
docker-compose -f docker-compose.full-stack.yml exec -T postgres psql -U postgres reddit_db < backup.sql
```

---

## 🔑 Environment Setup

### Full-Stack
```bash
cd backend/
cp .env.example .env
nano .env  # Edit with your values
docker-compose -f docker-compose.full-stack.yml up --build
```

### External Database
```bash
cd backend/
cat ENV_EXTERNAL_TEMPLATE.txt > .env.external
nano .env.external  # Edit with your database credentials
docker-compose --env-file .env.external -f docker-compose.external-db.yml up --build
```

### Generate secure keys
```bash
# Encryption key (32 bytes)
openssl rand -base64 32

# Secret key (64 bytes)
openssl rand -base64 64

# API key
openssl rand -base64 32
```

---

## 📊 Monitoring

### Watch logs in real-time
```bash
# All services
docker-compose -f docker-compose.full-stack.yml logs -f

# Specific service
docker-compose -f docker-compose.full-stack.yml logs -f backend

# Last 100 lines
docker-compose -f docker-compose.full-stack.yml logs --tail=100 backend
```

### Check service health
```bash
# Backend
curl http://localhost:8000/health

# Ollama
curl http://localhost:11434/api/tags

# OAuth
curl http://localhost:8001/health
```

### Monitor resource usage
```bash
# Real-time stats
docker stats

# Specific containers
docker stats coffee_backend coffee_frontend
```

---

## 🚨 Emergency Commands

### Stop everything immediately
```bash
# Full-stack
cd backend && docker-compose -f docker-compose.full-stack.yml down

# External DB
cd backend && docker-compose -f docker-compose.external-db.yml down

# All Docker Compose projects
docker-compose down
```

### Kill all running containers
```bash
docker kill $(docker ps -q)
```

### Remove all containers
```bash
docker rm -f $(docker ps -aq)
```

### Reset everything (nuclear option)
```bash
# Stop all
docker-compose down -v

# Clean system
docker system prune -a --volumes -f

# Rebuild
docker-compose up --build
```

---

## 📁 Quick Navigation

```bash
# Backend folder
cd /Users/iazam/nusoft/coffee-caption-generator/backend/

# Frontend folder
cd /Users/iazam/nusoft/coffee-caption-generator/frontend/

# Root folder
cd /Users/iazam/nusoft/coffee-caption-generator/
```

---

## 📚 Documentation References

- **Comprehensive Guide:** `DOCKER_DEPLOYMENT.md`
- **External Database:** `backend/EXTERNAL_DATABASE.md`
- **Quick Summary:** `DOCKER_SEPARATION_SUMMARY.txt`
- **Setup Summary:** `EXTERNAL_DB_SETUP_SUMMARY.md`
- **This Cheat Sheet:** `DOCKER_COMMANDS_CHEATSHEET.md`

---

## 💡 Pro Tips

1. **Use aliases** for frequently used commands:
   ```bash
   alias dcu='docker-compose up --build'
   alias dcd='docker-compose down'
   alias dcl='docker-compose logs -f'
   ```

2. **Check logs first** when troubleshooting:
   ```bash
   docker-compose logs --tail=50 backend
   ```

3. **Use detached mode** for production:
   ```bash
   docker-compose up -d
   ```

4. **Always rebuild** after code changes:
   ```bash
   docker-compose up --build
   ```

5. **Clean up regularly** to save disk space:
   ```bash
   docker system prune -a
   ```

---

**Happy Dockering! 🐳**

