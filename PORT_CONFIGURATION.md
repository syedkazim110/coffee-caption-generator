# 🔌 Port Configuration Guide

This guide explains how to configure ports using environment variables in Docker Compose.

---

## 📋 Available Port Environment Variables

All ports can be customized via environment variables. Here are the defaults:

| Service | Environment Variable | Default | Internal Port |
|---------|---------------------|---------|---------------|
| **Frontend** | `FRONTEND_PORT` | `3000` | `80` |
| **Backend API** | `API_PORT` | `8000` | `8000` |
| **OAuth Service** | `OAUTH_PORT` | `8001` | `8001` |
| **PostgreSQL (Main)** | `DB_PORT` | `5433` | `5432` |
| **PostgreSQL (OAuth)** | `OAUTH_DB_PORT` | `5435` | `5432` |
| **Ollama** | `OLLAMA_PORT` | `11434` | `11434` |

**Note:** Internal ports (inside containers) remain fixed. Only host ports can be changed.

---

## 🚀 Method 1: Environment File (Recommended)

Create a `.env` file in the `backend/` folder:

```bash
cd backend/
cat > .env << EOF
# Application Ports
API_PORT=8000
FRONTEND_PORT=3000
OAUTH_PORT=8001

# Database Ports
DB_PORT=5433
OAUTH_DB_PORT=5435

# Ollama Port
OLLAMA_PORT=11434
EOF
```

Docker Compose automatically loads `.env` files from the same directory.

**Start services:**
```bash
docker-compose -f docker-compose.full-stack.yml up --build
```

---

## 🔧 Method 2: Inline Environment Variables

Set ports directly in the command line:

```bash
cd backend/

# Single port
API_PORT=9000 docker-compose -f docker-compose.full-stack.yml up

# Multiple ports
API_PORT=9000 FRONTEND_PORT=4000 docker-compose -f docker-compose.full-stack.yml up

# Or export first
export API_PORT=9000
export FRONTEND_PORT=4000
docker-compose -f docker-compose.full-stack.yml up --build
```

---

## 📝 Method 3: Custom Environment File

Use a custom `.env` file with a different name:

```bash
# Create custom env file
cd backend/
cat > .env.custom << EOF
API_PORT=9000
FRONTEND_PORT=4000
DB_PORT=5433
OAUTH_DB_PORT=5435
EOF

# Load it explicitly
docker-compose --env-file .env.custom -f docker-compose.full-stack.yml up
```

---

## 💻 Method 4: Shell Export

Export variables in your shell session:

```bash
# Set variables
export API_PORT=9000
export FRONTEND_PORT=4000
export DB_PORT=5433
export OAUTH_DB_PORT=5435

# Start services (will use exported variables)
cd backend/
docker-compose -f docker-compose.full-stack.yml up --build
```

**Note:** Variables persist in your current shell session.

---

## 🌍 Method 5: System Environment Variables

Set system-wide environment variables (persists across sessions):

**macOS/Linux:**
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export API_PORT=9000' >> ~/.zshrc
echo 'export FRONTEND_PORT=4000' >> ~/.zshrc
source ~/.zshrc

# Or edit directly
nano ~/.zshrc
```

**Windows (PowerShell):**
```powershell
[System.Environment]::SetEnvironmentVariable('API_PORT', '9000', 'User')
[System.Environment]::SetEnvironmentVariable('FRONTEND_PORT', '4000', 'User')
```

---

## 📊 Example: Changing All Ports

**Step 1: Create `.env` file**
```bash
cd backend/
cat > .env << 'EOF'
# Use non-standard ports to avoid conflicts
API_PORT=9000
FRONTEND_PORT=4000
OAUTH_PORT=9001
DB_PORT=5433
OAUTH_DB_PORT=5435
OLLAMA_PORT=21434
EOF
```

**Step 2: Start services**
```bash
docker-compose -f docker-compose.full-stack.yml up --build
```

**Step 3: Access services**
- Frontend: http://localhost:4000
- Backend: http://localhost:9000
- OAuth: http://localhost:9001
- PostgreSQL (main): localhost:5433
- PostgreSQL (OAuth): localhost:5435
- Ollama: http://localhost:21434

---

## 🔍 Verifying Port Configuration

Check what ports are actually being used:

```bash
# Check running containers
docker-compose -f docker-compose.full-stack.yml ps

# Check port mappings
docker port coffee_backend
docker port coffee_frontend

# Or use docker ps
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

---

## 🎯 Use Cases

### 1. Port Conflict Resolution

If port 8000 is in use:
```bash
export API_PORT=9000
docker-compose -f docker-compose.full-stack.yml up
# Backend now on http://localhost:9000
```

### 2. Multiple Instances

Run multiple instances on different ports:
```bash
# Instance 1
API_PORT=8000 FRONTEND_PORT=3000 docker-compose -f docker-compose.full-stack.yml up

# Instance 2 (different terminal)
API_PORT=9000 FRONTEND_PORT=4000 docker-compose -f docker-compose.full-stack.yml up
```

### 3. Production Configuration

Use different ports for production:
```bash
# .env.production
API_PORT=80
FRONTEND_PORT=443
DB_PORT=5433
OAUTH_DB_PORT=5435

docker-compose --env-file .env.production -f docker-compose.full-stack.yml up
```

---

## ⚠️ Important Notes

### Internal Ports Cannot Change

The internal container ports (second number in `HOST:CONTAINER`) are fixed:
- Backend container always listens on port `8000` internally
- Frontend container always listens on port `80` internally
- PostgreSQL containers listen on port `5432` internally

You can only change the **host port** (first number).

### Frontend Backend Connection

When using Docker Compose with services on the same network:
- Frontend connects to backend via service name: `http://backend:8000`
- This works regardless of the host port mapping
- The `nginx.conf` uses `http://backend:8000` which is correct

### External Access

For external access (from your host machine):
- Use the **host port** (left side of mapping)
- Example: If `API_PORT=9000`, access via `http://localhost:9000`

---

## 🔐 Security Considerations

### Development
- Using high ports (8000+) is fine for development
- Environment variables in `.env` files are safe

### Production
- Consider using reverse proxy (nginx, Traefik)
- Don't expose database ports publicly
- Use firewall rules to restrict access
- Consider using secrets management for sensitive configs

---

## 📚 Quick Reference

### Check Port Availability

**macOS/Linux:**
```bash
lsof -i :8000
# or
netstat -an | grep 8000
```

**Kill process using port:**
```bash
# Find PID
lsof -ti :8000

# Kill it
kill -9 $(lsof -ti :8000)
```

### Change Single Port

```bash
cd backend/
API_PORT=9000 docker-compose -f docker-compose.full-stack.yml up
```

### Change Multiple Ports

```bash
cd backend/
API_PORT=9000 FRONTEND_PORT=4000 OAUTH_PORT=9001 \
  docker-compose -f docker-compose.full-stack.yml up
```

### Load from Custom File

```bash
cd backend/
docker-compose --env-file .env.custom -f docker-compose.full-stack.yml up
```

---

## 🐛 Troubleshooting

### Port Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Option 1: Use different port
API_PORT=9000 docker-compose up

# Option 2: Find and kill process
lsof -ti :8000 | xargs kill -9
```

### Environment Variable Not Working

**Check:**
1. Variable name is correct (case-sensitive)
2. `.env` file is in the same directory as `docker-compose.yml`
3. No spaces around `=` in `.env` file
4. Using `--env-file` flag if using custom file name

**Test:**
```bash
# Verify variable is set
echo $API_PORT

# Or check what Docker sees
docker-compose config | grep -A 5 ports
```

### Frontend Can't Reach Backend

**If using Docker Compose:**
- Frontend connects via service name `backend:8000`
- This is configured in `nginx.conf`
- No changes needed if both services in same compose file

**If running separately:**
- Set `BACKEND_URL` environment variable
- Frontend-only: `BACKEND_URL=http://localhost:8000 docker-compose up`
- Or update `nginx.conf` manually

---

## 📖 Additional Resources

- **Docker Compose Environment Variables**: https://docs.docker.com/compose/environment-variables/
- **Port Mapping**: https://docs.docker.com/compose/compose-file/compose-file-v3/#ports
- **Project Documentation**: `DOCKER_DEPLOYMENT.md`

---

## ✅ Summary

**Default Ports:**
- Frontend: `3000`
- Backend: `8000`
- OAuth: `8001`
- PostgreSQL (main): `5433`
- PostgreSQL (OAuth): `5435`
- Ollama: `11434`

**To Change:**
1. Create `.env` file with `PORT_NAME=new_port`
2. Or export: `export PORT_NAME=new_port`
3. Or inline: `PORT_NAME=new_port docker-compose up`

**Remember:**
- Only host ports can change (left side)
- Container ports are fixed (right side)
- Services in Docker network use service names, not host ports

