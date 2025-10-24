# OAuth Service Setup Instructions

## ✅ Completed Steps

1. **Environment Configuration**
   - `.env` file created with credentials
   - App ID: `805411348868649`
   - Encryption and security keys configured

---

## 🔧 Required Next Steps

### Step 1: ✅ OAuth Redirect URIs - No Action Needed!

**Good News:** `http://localhost` redirect URIs are **automatically allowed** while your app is in **Development Mode**. You don't need to manually add them!

Your configured redirect URIs will work automatically:
- ✅ `http://localhost:8001/api/v1/oauth/instagram/callback`
- ✅ `http://localhost:8001/api/v1/oauth/facebook/callback`

**Note:** When moving to production, you'll need to add your HTTPS redirect URIs manually (see Production section below).

### Step 2: Add Test Users (For Development Testing)

1. **Navigate to Roles:**
   - Left sidebar → **"Roles"** → **"Roles"**

2. **Add Test Users:**
   - Under "Test Users" section, click **"Add"**
   - Create 1-2 test users
   - These can access your app without App Review

3. **Add Instagram Tester (if needed):**
   - Go to **"Roles"** → **"Instagram Testers"**
   - Add your Instagram Business/Creator account
   - Accept the invite on Instagram app

---

## 🚀 Testing the OAuth Service

### Start the Service

**Option 1: Using Docker (Recommended)**
```bash
cd social-oauth-service
docker-compose up -d
```

**Option 2: Run Directly**
```bash
cd social-oauth-service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Initialize Database

The database schema is **automatically initialized** when you start the services!

```bash
# Start all services (database + Redis + OAuth service)
docker-compose up -d

# The database will automatically run the init_oauth_schema.sql migration
# You can verify it's working with:
docker-compose ps
docker-compose logs oauth-db
```

**Manual database access (if needed):**
```bash
# Connect to database
docker-compose exec oauth-db psql -U postgres -d oauth_db

# Or from your host machine (password: oauth_pass)
PGPASSWORD=oauth_pass psql -h localhost -p 5434 -U postgres -d oauth_db
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8001/health

# API documentation
# Open in browser: http://localhost:8001/docs
```

---

## 🔗 OAuth Flow Testing

### Instagram OAuth Flow

1. **Initiate OAuth (replace YOUR_USER_ID with a test ID):**
   ```
   http://localhost:8001/api/v1/oauth/instagram/authorize?user_id=test_user_123
   ```

2. **User will be redirected to Instagram login**
3. **After approval, user redirected back to your callback**
4. **Access token stored in database**

### Facebook OAuth Flow

1. **Initiate OAuth:**
   ```
   http://localhost:8001/api/v1/oauth/facebook/authorize?user_id=test_user_123
   ```

2. **User will be redirected to Facebook login**
3. **After approval, user redirected back to your callback**
4. **Access token stored in database**

---

## 📝 Important Notes

### For Development:
- ✅ Use test users to avoid App Review requirement
- ✅ Keep DEBUG=true in .env
- ✅ Use http://localhost URLs

### For Production (Later):
1. **Update .env file:**
   ```env
   DEBUG=false
   BASE_CALLBACK_URL=https://yourdomain.com
   INSTAGRAM_REDIRECT_URI=https://yourdomain.com/api/v1/oauth/instagram/callback
   FACEBOOK_REDIRECT_URI=https://yourdomain.com/api/v1/oauth/facebook/callback
   ```

2. **Update redirect URIs in Facebook Developer Portal** (use HTTPS)

3. **Submit for App Review** to get permissions for production users

4. **Switch app to "Live" mode** in Facebook Developer Portal

---

## 🔍 Troubleshooting

### "redirect_uri_mismatch" Error
- Ensure redirect URIs in `.env` exactly match those in Facebook Developer Portal
- No trailing slashes
- http vs https must match

### "Invalid Client ID" Error
- Verify App ID is correct: `805411348868649`
- Ensure App Secret is correct: `b213fc935b12b73d74697519ea649ffc`

### Database Connection Fails
```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs oauth-db
```

### Token Encryption Fails
- Ensure ENCRYPTION_KEY hasn't changed after storing tokens
- If you change the key, existing tokens cannot be decrypted

---

## 📚 Required Permissions

### Instagram Graph API
- `instagram_basic` - View basic account info
- `instagram_content_publish` - Publish content
- `pages_show_list` - List Facebook Pages
- `pages_read_engagement` - Read engagement metrics

### Facebook Login
- `pages_manage_posts` - Manage page posts
- `pages_read_engagement` - Read engagement
- `publish_to_groups` - Publish to groups (optional)

---

## ✅ Setup Checklist

- [x] `.env` file created with credentials
- [x] OAuth redirect URIs (automatically allowed in development mode)
- [ ] Test users created (optional but recommended)
- [ ] Instagram tester account added (if needed)
- [ ] Database initialized
- [ ] OAuth service running
- [ ] Test OAuth flow successful

---

## 🎯 Quick Commands Reference

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f oauth-service
docker-compose logs -f oauth-db

# Access database from container
docker-compose exec oauth-db psql -U postgres -d oauth_db

# Access database from host (password: oauth_pass)
PGPASSWORD=oauth_pass psql -h localhost -p 5434 -U postgres -d oauth_db

# Restart OAuth service after code changes
docker-compose restart oauth-service

# Rebuild and restart after code changes
docker-compose up -d --build oauth-service
```

---

## 📞 Support Resources

- **Facebook Developer Docs:** https://developers.facebook.com/docs/
- **Instagram Graph API:** https://developers.facebook.com/docs/instagram-api
- **OAuth 2.0 Flow:** https://developers.facebook.com/docs/facebook-login/guides/advanced/manual-flow

---

## What's Next?

1. ✅ Add redirect URIs in Facebook Developer Portal
2. ✅ Create test users
3. ✅ Start the OAuth service
4. ✅ Test the OAuth flow with a test account
5. ⏭️ Integrate with your main application
6. ⏭️ Submit for App Review when ready for production
