# Docker Setup Guide

## ✅ Docker Configuration Complete

Your Docker Compose setup is now fully configured to work with hashtags loading from the database.

## What Was Fixed

1. **Database Password**: Changed from `password` to `postgres123` (matches your local setup)
2. **Database Port**: Changed from `5434` to `5432` (standard PostgreSQL port)
3. **Schema Initialization**: Added `migration_schema.sql` to auto-create hashtag tables
4. **Data Migration**: Hashtag migration runs automatically on container startup
5. **Environment Variables**: Migration script now uses environment variables for Docker compatibility

## How to Run

### Start All Services
```bash
docker-compose up --build
```

This will:
1. ✅ Build and start PostgreSQL with hashtag schema
2. ✅ Build and start Ollama with phi3:mini model
3. ✅ Build and start web application
4. ✅ Automatically run hashtag migration (loads 219 hashtags)
5. ✅ Start the API server

### Stop All Services
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f
```

### Verify Hashtags Loaded
After containers are running:
```bash
docker exec -it coffee_web python test_hashtag_loading.py
```

## Service URLs

- **API**: http://localhost:8000
- **Ollama**: http://localhost:11434
- **PostgreSQL**: localhost:5432

## Database Connection

Inside Docker containers:
- Host: `postgres`
- Port: `5432`
- Database: `reddit_db`
- User: `postgres`
- Password: `postgres123`

From your local machine:
- Host: `localhost`
- Port: `5432`
- Database: `reddit_db`
- User: `postgres`
- Password: `postgres123`

## Troubleshooting

### Check if hashtags are loaded
```bash
docker exec -it coffee_postgres psql -U postgres -d reddit_db -c "SELECT COUNT(*) FROM hashtag_knowledge;"
```

### Manually run migration
```bash
docker exec -it coffee_web python migrate_data_to_postgres.py
```

### Check service health
```bash
docker-compose ps
```

## Notes

- First startup may take longer (downloading images, loading Ollama model)
- Hashtag migration runs automatically each time the web container starts
- Data persists in Docker volumes even after `docker-compose down`
- To completely reset data: `docker-compose down -v` (removes volumes)
