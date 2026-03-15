# AdvoLens — Deployment Guide

> **Navigation:** [Home](../README.md) | [Architecture](./architecture.md) | [API Reference](./api.md) | [ML Models](./ml-models.md) | Deployment | [Frontend](./frontend.md)

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables Reference](#environment-variables-reference)
- [Option 1: Local Development](#option-1-local-development)
- [Option 2: Docker (Local)](#option-2-docker-local)
- [Option 3: Render.com](#option-3-rendercom)
- [Option 4: VPS with Docker + Watchtower](#option-4-vps-with-docker--watchtower)
- [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
- [Database Setup (PostgreSQL + PostGIS)](#database-setup-postgresql--postgis)
- [CI/CD Pipeline](#cicd-pipeline)
- [VPS Management Commands](#vps-management-commands)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Backend
- Python **3.11+**
- PostgreSQL **14+** with **PostGIS** extension
- A [Cloudinary](https://cloudinary.com) account (free tier works)
- A [Google Gemini API key](https://ai.google.dev) (free tier available)

### Frontend
- Node.js **18+**
- npm **9+**

### Docker Deployment
- Docker **24+**
- Docker Compose (optional, for local stack)

---

## Environment Variables Reference

Copy `server/.env.example` to `server/.env` and fill in the values:

```bash
cp server/.env.example server/.env
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string with PostGIS | `postgresql://user:pass@host:5432/advolens` |
| `SECRET_KEY` | JWT signing secret (min 32 chars, random) | `openssl rand -hex 32` |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | `my-cloud` |
| `CLOUDINARY_API_KEY` | Cloudinary API key | `123456789012345` |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | `abcdefghijklmnopqrstuvwxyz` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALGORITHM` | JWT algorithm | `HS256` |
| `SMTP_EMAIL` | Gmail address for notifications | *(disabled if not set)* |
| `SMTP_PASSWORD` | Gmail App Password | *(disabled if not set)* |
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `465` |
| `EMAIL_MUNICIPALITY` | Municipality dept email | `municipality@city.gov.in` |
| `EMAIL_WATER_AUTHORITY` | Water authority email | `water@city.gov.in` |
| `EMAIL_KSEB` | KSEB dept email | `kseb@city.gov.in` |
| `EMAIL_PWD` | PWD dept email | `pwd@city.gov.in` |

### Getting a Gmail App Password

1. Enable 2-Factor Authentication on your Google account
2. Go to **Google Account → Security → 2-Step Verification → App passwords**
3. Create an app password for "Mail" / "Other"
4. Use that 16-character password as `SMTP_PASSWORD`

---

## Option 1: Local Development

Best for active development with hot-reload.

### 1. Set up PostgreSQL with PostGIS

```bash
# macOS
brew install postgresql postgis
brew services start postgresql

# Ubuntu / Debian
sudo apt install postgresql postgresql-contrib postgis
sudo systemctl start postgresql
```

Create the database:
```sql
psql postgres
CREATE DATABASE advolens;
\c advolens
CREATE EXTENSION postgis;
```

### 2. Set up Python environment

```bash
cd server
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install PyTorch (CPU-only, much smaller)
pip install torch==2.2.2+cpu torchvision==0.17.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Create an admin user

```bash
python -m app.scripts.create_admin
```

### 6. Start the backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### 7. Start the frontend

```bash
cd ../client
npm install
npm run dev
```

- Frontend: `http://localhost:3000`

---

## Option 2: Docker (Local)

### Build the image

```bash
# Using the provided script (macOS/Linux)
./scripts/build-local.sh

# Or manually
cd server
docker build -t advolens-backend:local .
```

### Run the container

```bash
docker run \
  -p 8000:8000 \
  --env-file server/.env \
  advolens-backend:local
```

### Run with Docker Compose (optional)

Create a `docker-compose.yml` in the project root:

```yaml
version: '3.8'

services:
  db:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_USER: advolens
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: advolens
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./server
    ports:
      - "8000:8000"
    env_file: ./server/.env
    environment:
      DATABASE_URL: postgresql://advolens:secret@db:5432/advolens
    depends_on:
      - db

volumes:
  pgdata:
```

```bash
docker compose up --build
```

---

## Option 3: Render.com

Render is the simplest cloud deployment option. A `render.yaml` is already included.

### Automatic deployment via render.yaml

```yaml
services:
  - type: web
    name: advolens-backend
    env: python
    rootDir: server
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn app.main:app --host 0.0.0.0 --port 8000"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
```

### Steps

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml`
5. Add all environment variables in the Render dashboard under **Environment**
6. Click **Deploy**

### Render Notes

- **Ephemeral filesystem:** Faiss index and uploaded files are not persisted between deploys. Use a Render **Disk** for persistent storage.
- **Cold starts:** Free tier services sleep after inactivity — the first request will be slow (~60s due to CLIP model loading).
- **Memory:** The CLIP model requires ~500MB RAM. Use at least the **Starter** plan.

### Add Persistent Disk (for Faiss index)

In `render.yaml`, add:

```yaml
disk:
  name: advolens-data
  mountPath: /app/data
  sizeGB: 1
```

Then update `server/app/ml/faiss_manager.py` to use `/app/data/` as the index path.

---

## Option 4: VPS with Docker + Watchtower

This is the production deployment setup used by the team — a Linux VPS (e.g., DigitalOcean, Hetzner, AWS EC2) running Docker with Watchtower for automatic deployments.

```mermaid
graph LR
    DEV[Developer\nlocal machine] -->|git push| GH[GitHub]
    GH -->|trigger| GHA[GitHub Actions\nbuild-and-push.yml]
    GHA -->|docker push| DH[Docker Hub\nsanjanamsanthoshsct/advolens-backend]
    DH -->|auto-pull every 5min| WT[Watchtower\non VPS]
    WT -->|restart| CTR[Docker Container\non VPS :8000]
```

### Initial VPS Setup

```bash
# 1. SSH into your VPS
ssh user@your-vps-ip

# 2. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 3. Install PostgreSQL with PostGIS
sudo apt install postgresql postgresql-contrib postgis

# 4. Create database
sudo -u postgres psql
CREATE DATABASE advolens;
\c advolens
CREATE EXTENSION postgis;

# 5. Create .env file
mkdir /opt/advolens
nano /opt/advolens/.env
# Paste your environment variables
```

### Deploy the Backend Container

```bash
# Pull the latest image
docker pull sanjanamsanthoshsct/advolens-backend:latest

# Run the container
docker run -d \
  --name advolens-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file /opt/advolens/.env \
  -v /opt/advolens/data:/app \
  sanjanamsanthoshsct/advolens-backend:latest
```

### Set up Watchtower (auto-deploy)

Watchtower polls Docker Hub every 5 minutes and restarts the container if a new image is available:

```bash
docker run -d \
  --name watchtower \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  --interval 300 \
  advolens-backend
```

### Set up Nginx Reverse Proxy (optional but recommended)

```bash
sudo apt install nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/advolens
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/advolens /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Add HTTPS with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Run Database Migrations on VPS

```bash
./scripts/vps-commands.sh migrate
# or manually:
docker exec -it advolens-backend alembic upgrade head
```

---

## Frontend Deployment (Vercel)

The Next.js frontend is deployed to Vercel.

### Steps

1. Go to [vercel.com](https://vercel.com) → **New Project**
2. Import your GitHub repository
3. Set **Root Directory** to `client`
4. Add environment variable:
   ```
   NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.onrender.com
   ```
5. Click **Deploy**

Vercel will automatically redeploy on every push to `main`.

### Frontend Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_BACKEND_URL` | Full URL of the FastAPI backend |

---

## Database Setup (PostgreSQL + PostGIS)

### Running Migrations

Alembic handles schema migrations. All migrations are in `server/alembic/versions/`.

```bash
cd server

# Apply all pending migrations
alembic upgrade head

# Check current migration version
alembic current

# View migration history
alembic history

# Roll back one migration
alembic downgrade -1
```

### Migration History

| Revision | Description |
|----------|-------------|
| `5356ca981e89` | Create issues table with PostGIS geometry |
| `bc70ba100bb7` | Add caption and tags columns to issues |
| `c1a2b3d4e5f6` | Add users and department tables |
| `de7656ac9346` | Add notifications table and citizen_token |
| `f1g2h3i4j5k6` | Add votes, comments, and engagement fields |

### Seeding Initial Data

```bash
# Create the first super admin user interactively
python -m app.scripts.create_admin

# Seed sample data (issues, users)
python -m app.scripts.seed_data
```

---

## CI/CD Pipeline

### GitHub Actions — Build & Push

**File:** `.github/workflows/build-and-push.yml`  
**Trigger:** Manual (`workflow_dispatch`)

```mermaid
graph LR
    TRIGGER[Manual trigger\n on GitHub Actions] --> CHECKOUT[Checkout code]
    CHECKOUT --> BUILDX[Set up Docker Buildx]
    BUILDX --> LOGIN[Login to Docker Hub\nusing secrets]
    LOGIN --> BUILD[Build & push\nlinux/amd64 image]
    BUILD --> DONE[Image pushed\nWatchtower auto-deploys]
```

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `DOCKER_USERNAME` | Docker Hub username |
| `DOCKER_PASSWORD` | Docker Hub password or access token |

### Triggering a Deployment

1. Go to **GitHub → Actions → Build and Push Docker Image**
2. Click **Run workflow**
3. Optionally enter a custom tag (default: `latest`)
4. Click **Run workflow**
5. Watchtower will pick up the new image within 5 minutes

### Building and Pushing Manually (macOS/Linux)

```bash
# Build and push to Docker Hub (for VPS deployment)
./scripts/build-and-push.sh

# Custom tag
DOCKER_TAG=v1.2.3 ./scripts/build-and-push.sh

# Build locally only (for testing)
./scripts/build-local.sh
```

---

## VPS Management Commands

The `scripts/vps-commands.sh` script provides helpful shortcuts:

```bash
# Usage
./scripts/vps-commands.sh <command>

# Available commands:
./scripts/vps-commands.sh seed          # Seed database with admin users
./scripts/vps-commands.sh create-admin  # Create a single admin user
./scripts/vps-commands.sh shell         # Open Python shell in container
./scripts/vps-commands.sh bash          # Open bash shell in container
./scripts/vps-commands.sh logs          # Stream container logs
./scripts/vps-commands.sh migrate       # Run database migrations
./scripts/vps-commands.sh restart       # Restart the container
./scripts/vps-commands.sh status        # Check container status
```

Set a custom container name:
```bash
CONTAINER_NAME=my-container ./scripts/vps-commands.sh logs
```

---

## Troubleshooting

### CLIP model not loading

**Symptom:** App crashes on startup with `RuntimeError: CLIP model not found`  
**Fix:** Ensure the container has internet access to download from HuggingFace Hub on first run. After the first download, the model is cached.

### PostGIS extension missing

**Symptom:** `ProgrammingError: type "geometry" does not exist`  
**Fix:**
```sql
\c advolens
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Alembic migration conflict

**Symptom:** `FAILED: Multiple head revisions`  
**Fix:**
```bash
alembic merge heads
alembic upgrade head
```

### Faiss index out of sync

**Symptom:** Duplicate detection not working after restart  
**Cause:** `faiss_index.bin` and `faiss_metadata.pkl` missing  
**Fix:** The index will rebuild automatically as new issues are submitted. If needed, rebuild from existing issues by re-running the embedding generation script.

### CORS errors in browser

**Symptom:** Frontend getting CORS errors when calling the backend  
**Fix:** Add your frontend URL to `CORS_ORIGINS` in `server/app/main.py`:
```python
allow_origins=[
    "http://localhost:3000",
    "https://your-frontend-domain.vercel.app",
    ...
],
```

### Email notifications not sending

**Symptom:** No emails received on new issue submission  
**Cause:** `SMTP_EMAIL` / `SMTP_PASSWORD` not set  
**Fix:** Configure Gmail App Password (see [Environment Variables](#environment-variables-reference)). The app continues to function normally without email — it just logs a warning.
