# Quick Start Without Docker

## 🎯 Running the VE Platform Without Docker

Since Docker Desktop is having issues, here's how to run everything directly:

---

## Step 1: Setup Supabase (Required)

### Option A: Use Supabase Cloud (Recommended)
1. Go to https://supabase.com
2. Create a free account
3. Create a new project
4. Wait for it to initialize (~2 minutes)
5. Go to Project Settings → API
6. Copy these values:
   - Project URL
   - `anon` `public` key
   - `service_role` `secret` key

### Option B: Skip Database for Now
You can test the API without a database, but most features won't work.

---

## Step 2: Configure Environment

I have updated `e:\MyCode\VE\.env.example` with your Supabase URL and Anon Key.

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. **CRITICAL:** Open `.env` and replace `your-supabase-service-key-from-dashboard` with your actual Service Role Key from the Supabase Dashboard (Project Settings -> API).

---

## Step 3: Run Backend

```bash
# Terminal 1: Backend API
cd e:\MyCode\VE\backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Test it:**
- Open http://localhost:8000
- Open http://localhost:8000/docs (API documentation)

---

## Step 4: Setup Database Schema

**✅ DONE!** I have already executed the database schema setup script on your Supabase project "VEdb". You don't need to do anything here.


---

## Step 5: Run User Frontend

```bash
# Terminal 2: User Frontend
cd e:\MyCode\VE\frontend
npm install
npm start
```

**Opens at:** http://localhost:3000

---

## Step 6: Run Admin Frontend

```bash
# Terminal 3: Admin Frontend
cd e:\MyCode\VE\admin-frontend
npm install
npm start
```

**Opens at:** http://localhost:3001

---

## ✅ Testing the Platform

### Test User Flow:
1. Open http://localhost:3000
2. Click "Sign Up"
3. Create an account
4. Browse marketplace
5. Hire a VE

### Test Admin Flow:
1. Open http://localhost:3001
2. Click "Create VE"
3. Fill out the wizard
4. See generated YAML

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
cd backend
pip install -r requirements.txt --force-reinstall
```

### Frontend won't start
```bash
# Clear cache
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Database connection errors
- Verify Supabase credentials in `.env`
- Make sure you ran the SQL schema
- Check Supabase project is active

### Port already in use
```bash
# Backend (port 8000)
netstat -ano | findstr :8000
# Kill the process or use different port:
uvicorn app.main:app --reload --port 8001

# Frontend (port 3000)
# Set PORT=3002 in frontend/.env
```

✅ Internet connection

---

## 🎉 Success Indicators

**Backend Running:**
```
✅ http://localhost:8000 shows: {"message": "VE SaaS Platform API"}
✅ http://localhost:8000/docs shows API documentation
✅ No errors in terminal
```

**Frontend Running:**
```
✅ http://localhost:3000 shows login page
✅ Can sign up and login
✅ Can browse marketplace
```

**Admin Running:**
```
✅ http://localhost:3001 shows admin interface
✅ Can access VE Creator
✅ Can generate YAML
```

---

## 🚀 Next Steps After Setup

1. Create your first VE in admin interface
2. Hire VEs in user interface
3. Set up Kubernetes + KAgent (when ready)
4. Configure Agent Gateway (when ready)

---

**You're all set! No Docker needed.** 🎊
