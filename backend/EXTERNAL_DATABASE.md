# 🌐 External Database Setup Guide

This guide explains how to run the Coffee Caption Generator with an external managed database service (AWS RDS, Azure Database, Google Cloud SQL, etc.) instead of a local PostgreSQL container.

## 📋 Overview

The `docker-compose.external-db.yml` file runs:
- ✅ **Backend API** (connects to external database)
- ✅ **Frontend** (nginx)
- ✅ **Ollama** (local LLM)
- ✅ **OAuth Service** (connects to external database)
- ❌ **No PostgreSQL containers** (uses your external database)

## 🎯 When to Use This

- **Production deployments** with managed databases
- **AWS RDS**, Azure Database for PostgreSQL, Google Cloud SQL
- **Scaling** - separate database scaling from application scaling
- **High availability** - use managed database HA features
- **Compliance** - use enterprise database security features

---

## 🚀 Quick Start

### Step 1: Prepare External Database

Your external PostgreSQL database must be initialized with the required schemas:

**Main Database:**
```sql
-- Run these SQL files in order:
1. init.sql
2. init_brand_schema.sql
3. migration_schema.sql
4. add_api_key_management.sql
5. add_preferred_llm_model.sql
```

**OAuth Database (if separate):**
```sql
-- Run this SQL file:
../social-oauth-service/migrations/init_oauth_schema.sql
```

### Step 2: Create Environment File

Create `.env.external` in the `backend/` folder:

```bash
cd backend/
cp .env.external.example .env.external
# Edit .env.external with your database credentials
```

**Minimum required variables:**
```env
# Main Database (REQUIRED)
DB_HOST=your-db-host.rds.amazonaws.com
DB_NAME=reddit_db
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Security (REQUIRED)
ENCRYPTION_KEY=your-32-byte-key
SECRET_KEY=your-secret-key
OAUTH_SERVICE_API_KEY=your-service-key
```

### Step 3: Configure Network Access

Ensure your Docker host can reach the external database:

**AWS RDS:**
- Add inbound rule to security group: Port 5432 from Docker host IP
- Or enable public accessibility (not recommended for production)

**Azure Database:**
- Add firewall rule for Docker host IP
- Enable "Allow access to Azure services" if needed

**Google Cloud SQL:**
- Add authorized network for Docker host IP
- Or use Cloud SQL Proxy

### Step 4: Start Services

```bash
cd backend/
docker-compose --env-file .env.external -f docker-compose.external-db.yml up --build -d
```

### Step 5: Verify Connection

```bash
# Check backend logs
docker-compose -f docker-compose.external-db.yml logs backend

# Test health endpoint
curl http://localhost:8000/health

# Should show database connection status
```

---

## ⚙️ Configuration Options

### Database SSL/TLS

For production, always use SSL:

```env
DB_SSL_MODE=require
```

**SSL Mode Options:**
- `disable` - No SSL (dev only)
- `allow` - Try SSL, fall back to non-SSL
- `prefer` - Prefer SSL, but allow non-SSL
- `require` - Require SSL ✅ (recommended)
- `verify-ca` - Require SSL and verify certificate
- `verify-full` - Require SSL and verify certificate + hostname

### Separate OAuth Database

If using a separate database for OAuth:

```env
OAUTH_DB_HOST=oauth-db.rds.amazonaws.com
OAUTH_DB_NAME=oauth_db
OAUTH_DB_USER=oauth_user
OAUTH_DB_PASSWORD=oauth_password
```

If not specified, OAuth will use the main database.

### External Ollama Service

To use an external Ollama service instead of local:

```env
OLLAMA_URL=https://your-ollama-service.com
```

Then remove the `ollama` service from the compose file or set:
```yaml
depends_on: []  # Remove ollama dependency
```

---

## 🌩️ Cloud Provider Examples

### AWS RDS PostgreSQL

**1. Create RDS Instance:**
```bash
aws rds create-db-instance \
  --db-instance-identifier coffee-caption-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username postgres \
  --master-user-password YourSecurePassword \
  --allocated-storage 20 \
  --publicly-accessible \
  --vpc-security-group-ids sg-xxxxx
```

**2. Get Endpoint:**
```bash
aws rds describe-db-instances \
  --db-instance-identifier coffee-caption-db \
  --query 'DBInstances[0].Endpoint.Address'
```

**3. Configure .env.external:**
```env
DB_HOST=coffee-caption-db.abc123.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=reddit_db
DB_USER=postgres
DB_PASSWORD=YourSecurePassword
DB_SSL_MODE=require
```

**4. Initialize Database:**
```bash
# Connect to RDS and run init scripts
psql -h coffee-caption-db.abc123.us-east-1.rds.amazonaws.com \
     -U postgres -d reddit_db < init.sql
```

### Azure Database for PostgreSQL

**1. Create Azure Database:**
```bash
az postgres server create \
  --resource-group myResourceGroup \
  --name coffee-caption-db \
  --location eastus \
  --admin-user postgres \
  --admin-password YourSecurePassword \
  --sku-name B_Gen5_1 \
  --version 15
```

**2. Configure Firewall:**
```bash
az postgres server firewall-rule create \
  --resource-group myResourceGroup \
  --server-name coffee-caption-db \
  --name AllowDockerHost \
  --start-ip-address YOUR_DOCKER_HOST_IP \
  --end-ip-address YOUR_DOCKER_HOST_IP
```

**3. Configure .env.external:**
```env
DB_HOST=coffee-caption-db.postgres.database.azure.com
DB_PORT=5432
DB_NAME=reddit_db
DB_USER=postgres@coffee-caption-db
DB_PASSWORD=YourSecurePassword
DB_SSL_MODE=require
```

### Google Cloud SQL

**1. Create Cloud SQL Instance:**
```bash
gcloud sql instances create coffee-caption-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

**2. Set Password:**
```bash
gcloud sql users set-password postgres \
  --instance=coffee-caption-db \
  --password=YourSecurePassword
```

**3. Get IP Address:**
```bash
gcloud sql instances describe coffee-caption-db \
  --format="value(ipAddresses[0].ipAddress)"
```

**4. Configure .env.external:**
```env
DB_HOST=34.123.45.67
DB_PORT=5432
DB_NAME=reddit_db
DB_USER=postgres
DB_PASSWORD=YourSecurePassword
DB_SSL_MODE=require
```

---

## 🔧 Database Initialization

### Option 1: Manual Initialization

Connect to your external database and run SQL files:

```bash
# Set connection variables
export PGHOST=your-db-host.rds.amazonaws.com
export PGPORT=5432
export PGDATABASE=reddit_db
export PGUSER=postgres
export PGPASSWORD=your_password

# Run initialization scripts
psql -f init.sql
psql -f init_brand_schema.sql
psql -f migration_schema.sql
psql -f add_api_key_management.sql
psql -f add_preferred_llm_model.sql

# For OAuth database (if separate)
psql -d oauth_db -f ../social-oauth-service/migrations/init_oauth_schema.sql
```

### Option 2: Automated Initialization Script

Create `init_external_db.sh`:

```bash
#!/bin/bash
set -e

# Load environment variables
source .env.external

echo "Initializing external database..."
echo "Host: $DB_HOST"
echo "Database: $DB_NAME"

# Run SQL files
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -f init.sql \
  -f init_brand_schema.sql \
  -f migration_schema.sql \
  -f add_api_key_management.sql \
  -f add_preferred_llm_model.sql

echo "Database initialized successfully!"
```

Make it executable and run:
```bash
chmod +x init_external_db.sh
./init_external_db.sh
```

---

## 📊 Common Commands

### Start Services
```bash
cd backend/
docker-compose --env-file .env.external -f docker-compose.external-db.yml up -d
```

### View Logs
```bash
docker-compose -f docker-compose.external-db.yml logs -f backend
```

### Stop Services
```bash
docker-compose -f docker-compose.external-db.yml down
```

### Restart Backend Only
```bash
docker-compose -f docker-compose.external-db.yml restart backend
```

### Test Database Connection
```bash
# From Docker host
docker-compose -f docker-compose.external-db.yml exec backend \
  python -c "import psycopg2; conn=psycopg2.connect(host='$DB_HOST', database='$DB_NAME', user='$DB_USER', password='$DB_PASSWORD'); print('Connected!')"
```

---

## 🐛 Troubleshooting

### Connection Refused

**Problem:** Backend can't connect to external database

**Solutions:**
```bash
# 1. Check network connectivity
ping your-db-host.rds.amazonaws.com

# 2. Check firewall rules
# AWS: Security group inbound rules
# Azure: Firewall rules
# GCP: Authorized networks

# 3. Verify credentials
psql -h your-db-host -U postgres -d reddit_db

# 4. Check SSL requirements
# Try with sslmode=disable for testing (not for production!)
```

### SSL Certificate Errors

**Problem:** SSL verification fails

**Solutions:**
```env
# Option 1: Use require mode (verifies encryption, not certificate)
DB_SSL_MODE=require

# Option 2: Disable SSL for testing (dev only)
DB_SSL_MODE=disable

# Option 3: Download and verify CA certificate
# For RDS: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html
DB_SSL_MODE=verify-full
```

### Timeout Issues

**Problem:** Connection times out

**Solutions:**
```bash
# 1. Check if database is publicly accessible
# AWS RDS: Check "Publicly accessible" setting

# 2. Check VPC/subnet configuration
# Ensure Docker host and database are in compatible networks

# 3. Use connection pooling
# Consider PgBouncer for better connection management

# 4. Increase timeout
docker-compose -f docker-compose.external-db.yml up \
  -e DB_CONNECT_TIMEOUT=30
```

### Schema Missing

**Problem:** Tables don't exist

**Solutions:**
```bash
# 1. Verify initialization ran successfully
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dt"

# 2. Re-run initialization
./init_external_db.sh

# 3. Check for errors in init scripts
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f init.sql
```

---

## 🔒 Security Best Practices

### Database Security

- ✅ Use SSL/TLS (`DB_SSL_MODE=require`)
- ✅ Strong passwords (32+ characters, mixed case, numbers, symbols)
- ✅ Restrict network access (specific IP ranges, not 0.0.0.0/0)
- ✅ Use least-privilege database users
- ✅ Enable database audit logging
- ✅ Regular security patches and updates
- ✅ Encrypted backups

### Application Security

```env
# Use strong, unique keys
ENCRYPTION_KEY=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 64)
OAUTH_SERVICE_API_KEY=$(openssl rand -base64 32)
```

### Network Security

- ✅ Use VPC peering or private links
- ✅ Enable connection encryption
- ✅ Use secrets management (AWS Secrets Manager, Azure Key Vault, etc.)
- ✅ Rotate credentials regularly
- ✅ Monitor for suspicious activity

---

## 📈 Performance Optimization

### Connection Pooling

For high-traffic applications, use PgBouncer:

```yaml
# Add to docker-compose.external-db.yml
pgbouncer:
  image: pgbouncer/pgbouncer:latest
  environment:
    - DATABASES_HOST=${DB_HOST}
    - DATABASES_PORT=${DB_PORT}
    - DATABASES_DBNAME=${DB_NAME}
    - DATABASES_USER=${DB_USER}
    - DATABASES_PASSWORD=${DB_PASSWORD}
  ports:
    - "6432:6432"

# Update backend to use pgbouncer
backend:
  environment:
    - DB_HOST=pgbouncer
    - DB_PORT=6432
```

### Database Tuning

**RDS Parameter Group:**
```sql
-- Increase connection limit
max_connections = 100

-- Optimize work memory
work_mem = 16MB
shared_buffers = 256MB

-- Enable query logging (dev only)
log_statement = 'all'
log_duration = on
```

---

## 💰 Cost Optimization

### AWS RDS

- Use `db.t3.micro` or `db.t4g.micro` for development
- Use Reserved Instances for production (up to 72% savings)
- Enable Multi-AZ only for production
- Use automated backups with appropriate retention
- Consider Aurora Serverless for variable workloads

### Azure Database

- Use Basic tier for development
- Use General Purpose tier for production
- Enable auto-scaling for storage
- Use read replicas for read-heavy workloads

### Google Cloud SQL

- Use `db-f1-micro` for development
- Use `db-n1-standard-1` for production
- Enable automatic storage increase
- Use high availability only when needed

---

## 📚 Additional Resources

- **AWS RDS Documentation:** https://docs.aws.amazon.com/rds/
- **Azure Database Documentation:** https://docs.microsoft.com/azure/postgresql/
- **Google Cloud SQL Documentation:** https://cloud.google.com/sql/docs
- **PostgreSQL SSL Documentation:** https://www.postgresql.org/docs/current/ssl-tcp.html

---

## 🎯 Quick Reference

**Start with external database:**
```bash
cd backend/
docker-compose --env-file .env.external -f docker-compose.external-db.yml up -d
```

**Stop services:**
```bash
docker-compose -f docker-compose.external-db.yml down
```

**View logs:**
```bash
docker-compose -f docker-compose.external-db.yml logs -f
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

