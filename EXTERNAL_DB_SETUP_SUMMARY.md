# 🌐 External Database Setup - Quick Reference

This document provides a quick reference for deploying Coffee Caption Generator with an external database (AWS RDS, Azure Database, Google Cloud SQL, etc.).

---

## 📋 What's New

✅ **New Docker Compose File:** `backend/docker-compose.external-db.yml`  
✅ **Comprehensive Guide:** `backend/EXTERNAL_DATABASE.md`  
✅ **Environment Template:** `backend/ENV_EXTERNAL_TEMPLATE.txt`  
✅ **Updated Documentation:** All deployment docs updated with external DB option

---

## 🚀 Quick Start (5 Steps)

### 1. Prepare External Database

Create a PostgreSQL database on your cloud provider (AWS RDS, Azure, GCP, etc.)

**Minimum Requirements:**
- PostgreSQL 13+
- SSL/TLS enabled
- Network access from Docker host

### 2. Initialize Database Schemas

Run these SQL files on your external database **in order**:

```bash
# Connect to your database
psql -h your-db-host.rds.amazonaws.com -U postgres -d reddit_db

# Run initialization scripts (from backend/ folder)
\i init.sql
\i init_brand_schema.sql
\i migration_schema.sql
\i add_api_key_management.sql
\i add_preferred_llm_model.sql

# For OAuth database (if separate)
\c oauth_db
\i ../social-oauth-service/migrations/init_oauth_schema.sql
```

### 3. Create Environment File

```bash
cd backend/

# Create .env.external from template
cat ENV_EXTERNAL_TEMPLATE.txt > .env.external

# Edit with your credentials
nano .env.external
```

**Required Variables:**
```env
DB_HOST=your-db.rds.amazonaws.com
DB_NAME=reddit_db
DB_USER=postgres
DB_PASSWORD=YourSecurePassword
DB_SSL_MODE=require

ENCRYPTION_KEY=your-32-byte-encryption-key
SECRET_KEY=your-secret-key
OAUTH_SERVICE_API_KEY=your-api-key
```

### 4. Configure Network Access

**AWS RDS:**
- Add inbound rule in Security Group: PostgreSQL (5432) from Docker host IP

**Azure Database:**
- Add firewall rule for Docker host IP

**Google Cloud SQL:**
- Add authorized network for Docker host IP

### 5. Start Services

```bash
cd backend/

# Start all services (backend, frontend, ollama, oauth)
docker-compose --env-file .env.external -f docker-compose.external-db.yml up --build -d

# View logs
docker-compose -f docker-compose.external-db.yml logs -f

# Check health
curl http://localhost:8000/health
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📦 What Gets Deployed

### Included Services:
- ✅ **Frontend** (Nginx on port 3000)
- ✅ **Backend API** (FastAPI on port 8000)
- ✅ **Ollama** (Local LLM on port 11434)
- ✅ **OAuth Service** (Port 8001)

### External Services (You Provide):
- ❌ **PostgreSQL** (Main database - AWS RDS, Azure, etc.)
- ❌ **PostgreSQL** (OAuth database - can be same as main)

---

## 🔒 Security Checklist

- [ ] Use strong, unique passwords (32+ characters)
- [ ] Enable SSL/TLS (`DB_SSL_MODE=require`)
- [ ] Restrict network access (specific IP ranges)
- [ ] Generate secure encryption keys
- [ ] Use secrets management (AWS Secrets Manager, etc.)
- [ ] Enable database audit logging
- [ ] Set up automated backups
- [ ] Rotate credentials regularly

**Generate Secure Keys:**
```bash
# Encryption key (32 bytes base64)
openssl rand -base64 32

# Secret key (64 bytes base64)
openssl rand -base64 64

# Service API key
openssl rand -base64 32
```

---

## 🐛 Troubleshooting

### Connection Refused

```bash
# Test connectivity
ping your-db-host.rds.amazonaws.com

# Test PostgreSQL connection
psql -h your-db-host -U postgres -d reddit_db

# Check Docker logs
docker-compose -f docker-compose.external-db.yml logs backend
```

### SSL Errors

```env
# For testing only - disable SSL
DB_SSL_MODE=disable

# Production - require SSL
DB_SSL_MODE=require
```

### Schema Missing

```bash
# Verify tables exist
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dt"

# Re-run initialization
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f init.sql
```

---

## 💰 Cost Optimization

### AWS RDS
- **Dev:** db.t3.micro ($15-20/month)
- **Prod:** db.t3.small or Reserved Instances (up to 72% savings)
- Enable automated backups with 7-day retention

### Azure Database
- **Dev:** Basic tier ($25-30/month)
- **Prod:** General Purpose tier with auto-scaling

### Google Cloud SQL
- **Dev:** db-f1-micro ($10-15/month)
- **Prod:** db-n1-standard-1 with high availability

---

## 📊 Common Commands

```bash
# Navigate to backend
cd backend/

# Start services
docker-compose --env-file .env.external -f docker-compose.external-db.yml up -d

# View logs (all services)
docker-compose -f docker-compose.external-db.yml logs -f

# View logs (specific service)
docker-compose -f docker-compose.external-db.yml logs -f backend

# Restart backend only
docker-compose -f docker-compose.external-db.yml restart backend

# Stop services
docker-compose -f docker-compose.external-db.yml down

# Stop and remove volumes (keeps external DB data)
docker-compose -f docker-compose.external-db.yml down -v

# Check service health
docker-compose -f docker-compose.external-db.yml ps
curl http://localhost:8000/health
```

---

## 📚 Cloud Provider Examples

### AWS RDS

**1. Create RDS Instance:**
```bash
aws rds create-db-instance \
  --db-instance-identifier coffee-db \
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
  --db-instance-identifier coffee-db \
  --query 'DBInstances[0].Endpoint.Address'
```

**3. Configure:**
```env
DB_HOST=coffee-db.abc123.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=reddit_db
DB_USER=postgres
DB_PASSWORD=YourSecurePassword
DB_SSL_MODE=require
```

### Azure Database for PostgreSQL

**1. Create Database:**
```bash
az postgres server create \
  --resource-group myResourceGroup \
  --name coffee-db \
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
  --server-name coffee-db \
  --name AllowDockerHost \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP
```

**3. Configure:**
```env
DB_HOST=coffee-db.postgres.database.azure.com
DB_PORT=5432
DB_NAME=reddit_db
DB_USER=postgres@coffee-db
DB_PASSWORD=YourSecurePassword
DB_SSL_MODE=require
```

### Google Cloud SQL

**1. Create Instance:**
```bash
gcloud sql instances create coffee-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

**2. Set Password:**
```bash
gcloud sql users set-password postgres \
  --instance=coffee-db \
  --password=YourSecurePassword
```

**3. Get IP:**
```bash
gcloud sql instances describe coffee-db \
  --format="value(ipAddresses[0].ipAddress)"
```

**4. Configure:**
```env
DB_HOST=34.123.45.67
DB_PORT=5432
DB_NAME=reddit_db
DB_USER=postgres
DB_PASSWORD=YourSecurePassword
DB_SSL_MODE=require
```

---

## 🎯 Deployment Checklist

- [ ] External database created and accessible
- [ ] Database schemas initialized (all .sql files)
- [ ] Network/firewall rules configured
- [ ] `.env.external` file created with credentials
- [ ] SSL/TLS enabled and tested
- [ ] Security keys generated and stored securely
- [ ] Backup strategy configured
- [ ] Monitoring and alerting set up
- [ ] Docker compose file tested
- [ ] Health checks passing

---

## 📖 Additional Resources

- **Complete Guide:** `backend/EXTERNAL_DATABASE.md` (12KB, comprehensive)
- **Deployment Options:** `DOCKER_DEPLOYMENT.md` (all deployment modes)
- **Quick Reference:** `DOCKER_SEPARATION_SUMMARY.txt` (quick commands)
- **Environment Template:** `backend/ENV_EXTERNAL_TEMPLATE.txt` (copy to .env.external)

**Cloud Provider Documentation:**
- AWS RDS: https://docs.aws.amazon.com/rds/
- Azure Database: https://docs.microsoft.com/azure/postgresql/
- Google Cloud SQL: https://cloud.google.com/sql/docs

---

## ✅ Success Indicators

Your deployment is successful when:

1. ✅ All containers are running:
   ```bash
   docker-compose -f docker-compose.external-db.yml ps
   # All services show "Up" status
   ```

2. ✅ Backend connects to database:
   ```bash
   docker-compose -f docker-compose.external-db.yml logs backend | grep "connected"
   ```

3. ✅ Health check passes:
   ```bash
   curl http://localhost:8000/health
   # Returns: {"status": "healthy"}
   ```

4. ✅ Frontend is accessible:
   - Visit: http://localhost:3000
   - API Docs: http://localhost:8000/docs

---

## 🆘 Getting Help

If you encounter issues:

1. **Check logs:** `docker-compose -f docker-compose.external-db.yml logs -f`
2. **Verify database connection:** Test with `psql` from Docker host
3. **Review documentation:** `backend/EXTERNAL_DATABASE.md`
4. **Check network access:** Verify firewall rules and security groups
5. **Validate environment:** Ensure all required variables in `.env.external`

---

**Ready to deploy? Start with Step 1 above! 🚀**

