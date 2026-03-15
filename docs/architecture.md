# AdvoLens — System Architecture

> **Navigation:** [Home](../README.md) | Architecture | [API Reference](./api.md) | [ML Models](./ml-models.md) | [Deployment](./deployment.md) | [Frontend](./frontend.md)

---

## Table of Contents

- [High-Level Overview](#high-level-overview)
- [Component Architecture](#component-architecture)
- [Request Lifecycle — Issue Submission](#request-lifecycle--issue-submission)
- [Data Flow Diagram](#data-flow-diagram)
- [Application Layers](#application-layers)
- [Database Schema](#database-schema)
- [Authentication & Authorization](#authentication--authorization)
- [Service Dependencies](#service-dependencies)
- [Deployment Architecture](#deployment-architecture)

---

## High-Level Overview

AdvoLens is built as a three-tier web application with an integrated AI/ML pipeline:

```mermaid
graph TB
    subgraph "Client Layer"
        PWA["Next.js PWA\n(Vercel)"]
    end

    subgraph "API Layer"
        BE["FastAPI Backend\n(Render.com / Docker)"]
    end

    subgraph "AI/ML Layer"
        CLIP["CLIP\nImage Embeddings"]
        GEM["Gemini API\nCaptioning + Tags"]
        FAISS["Faiss Index\nSimilarity Search"]
        DBSCAN["DBSCAN\nGeo-Clustering"]
    end

    subgraph "Data Layer"
        PG["PostgreSQL + PostGIS\n(Cloud SQL)"]
        CDN["Cloudinary\nImage Storage"]
    end

    subgraph "Notification Layer"
        EMAIL["SMTP Email\n(Gmail)"]
        NOTIF["In-App Notifications\n(DB-backed)"]
    end

    PWA -->|"HTTPS REST"| BE
    BE --> CLIP
    BE --> GEM
    BE --> FAISS
    BE --> DBSCAN
    BE --> PG
    BE --> CDN
    BE --> EMAIL
    BE --> NOTIF
```

---

## Component Architecture

```mermaid
graph LR
    subgraph "Frontend (Next.js)"
        direction TB
        Pages["App Pages\n/report /feed\n/admin /notifications"]
        API_Routes["Next.js API Routes\n(proxy layer)"]
        Components["UI Components\nIssueMap, Charts"]
        LibAPI["lib/api.ts\n(Axios client)"]

        Pages --> LibAPI
        Pages --> Components
        LibAPI --> API_Routes
    end

    subgraph "Backend (FastAPI)"
        direction TB
        Main["main.py\n(App factory)"]
        
        subgraph "API Routers"
            IssuesR["/issues"]
            AuthR["/auth"]
            AdminR["/admin"]
            NotifR["/notifications"]
            AnalyticsR["/analytics"]
            EngageR["/issues (engagement)"]
        end

        subgraph "Core"
            DB["database.py\n(SQLAlchemy)"]
            Auth["auth.py\n(JWT)"]
            Security["security.py\n(get_current_user)"]
        end

        subgraph "ML Pipeline"
            CLIP_S["clip_service.py"]
            GEM_S["gemini_service.py"]
            FAISS_S["faiss_manager.py"]
            GEO_S["geo_clustering.py"]
        end

        subgraph "Services"
            Cloud["cloudinary_service.py"]
            Email["email_service.py"]
            Route["routing_service.py"]
            GeoSvc["geo_service.py"]
            NotifSvc["notification.py"]
        end

        Main --> IssuesR
        Main --> AuthR
        Main --> AdminR
        Main --> NotifR
        Main --> AnalyticsR
        Main --> EngageR
        IssuesR --> CLIP_S
        IssuesR --> GEM_S
        IssuesR --> FAISS_S
        IssuesR --> Route
        IssuesR --> Cloud
        IssuesR --> Email
        AnalyticsR --> GEO_S
    end

    API_Routes -->|HTTP| Main
```

---

## Request Lifecycle — Issue Submission

The most complex flow in the system is when a citizen submits a new issue. Here is the full end-to-end pipeline:

```mermaid
sequenceDiagram
    participant C as Citizen (Browser)
    participant FE as Next.js Frontend
    participant BE as FastAPI Backend
    participant CDN as Cloudinary
    participant CLIP as CLIP Model
    participant GEM as Gemini API
    participant FAISS as Faiss Index
    participant PG as PostgreSQL
    participant EMAIL as SMTP Email

    C->>FE: Upload photo + GPS coords
    FE->>BE: POST /issues/ (multipart/form-data)
    
    Note over BE: 1. Generate citizen tracking token

    BE->>CDN: Upload image file
    CDN-->>BE: Secure image URL

    BE->>CLIP: Generate 512-dim embedding
    CLIP-->>BE: Normalized embedding vector

    BE->>GEM: Analyze image (caption + tags)
    GEM-->>BE: {"caption": "...", "tags": [...]}

    BE->>FAISS: Search for similar vectors (threshold=0.92)
    FAISS-->>BE: [(issue_id, score), ...]

    BE->>PG: Find issues within 50m radius (PostGIS)
    PG-->>BE: Nearby issue IDs

    Note over BE: Combine visual + spatial duplicate check

    BE->>BE: Auto-assign department via routing_service
    BE->>PG: INSERT new issue record
    PG-->>BE: new_issue (with ID)

    BE->>FAISS: Add embedding to index
    BE->>PG: INSERT notification (issue_created)

    opt Duplicate detected
        BE->>PG: INSERT notification (duplicate_detected)
    end

    BE->>EMAIL: Notify department officials (async)
    BE-->>FE: IssueCreateResponse + tracking_token

    FE->>C: Show confirmation + save token to localStorage
```

---

## Data Flow Diagram

```mermaid
flowchart TD
    A[Citizen submits photo + GPS] --> B[FastAPI receives request]
    B --> C[Save image to /tmp]
    C --> D[Upload to Cloudinary]
    C --> E[Generate CLIP embedding]
    C --> F[Gemini image analysis]
    D --> G[Get cloud image URL]
    E --> H[Search Faiss index]
    F --> I[Extract caption & tags]
    H --> J{Visual duplicate?}
    B --> K[PostGIS radius query 50m]
    K --> L{Spatial duplicate?}
    J -- Yes --> M{Both visual + spatial?}
    L -- Yes --> M
    M -- Yes --> N[Mark as DEFINITE duplicate]
    M -- No --> O[Flag as possible duplicate]
    J -- No --> P[No duplicate]
    L -- No --> P
    I --> Q[routing_service: assign department]
    G & I & Q & N --> R[Save Issue to PostgreSQL]
    R --> S[Add embedding to Faiss]
    R --> T[Create in-app notification]
    R --> U[Send email to department]
    R --> V[Return tracking token to citizen]
```

---

## Application Layers

The backend follows a clean layered architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (routers)                   │
│   issues.py | auth.py | admin.py | notifications.py     │
│   analytics.py | engagement.py                          │
├─────────────────────────────────────────────────────────┤
│                  Business Logic Layer                    │
│   ML Pipeline: clip_service → faiss_manager →           │
│               gemini_service → routing_service          │
│   Services: cloudinary | email | geo | notification      │
├─────────────────────────────────────────────────────────┤
│                    CRUD Layer                            │
│   crud/issue.py — database access functions             │
├─────────────────────────────────────────────────────────┤
│                    Data Layer                            │
│   SQLAlchemy models (Issue, User, Notification,         │
│   Vote, Comment) backed by PostgreSQL + PostGIS         │
├─────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                    │
│   PostgreSQL | Cloudinary | SMTP | Faiss index file     │
└─────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Files | Responsibility |
|-------|-------|----------------|
| **API** | `app/api/*.py` | Route handlers, request validation, HTTP responses |
| **Core** | `app/core/*.py` | Config, DB session factory, JWT auth, security deps |
| **ML** | `app/ml/*.py` | CLIP, Gemini, Faiss, DBSCAN — stateless singletons |
| **Services** | `app/services/*.py` | External integrations (Cloudinary, email, geo) |
| **CRUD** | `app/crud/*.py` | Database read/write operations via SQLAlchemy |
| **Models** | `app/models/*.py` | SQLAlchemy ORM table definitions |
| **Schemas** | `app/schemas/*.py` | Pydantic models for request/response validation |

---

## Database Schema

```mermaid
erDiagram
    ISSUES {
        int id PK
        string title
        string description
        string image_url
        string status
        string caption
        string[] tags
        enum department
        string citizen_token
        int upvote_count
        int priority_score
        geometry location
        timestamp created_at
        timestamp updated_at
    }

    USERS {
        int id PK
        string email UK
        string hashed_password
        string name
        enum role
        enum department
    }

    NOTIFICATIONS {
        int id PK
        int issue_id FK
        string type
        string message
        bool is_read
        string citizen_token
        timestamp created_at
    }

    VOTES {
        int id PK
        int issue_id FK
        string citizen_token
        string vote_type
        timestamp created_at
    }

    COMMENTS {
        int id PK
        int issue_id FK
        string citizen_token
        string text
        timestamp created_at
    }

    ISSUES ||--o{ NOTIFICATIONS : "has"
    ISSUES ||--o{ VOTES : "has"
    ISSUES ||--o{ COMMENTS : "has"
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **PostGIS geometry column** | Enables native spatial queries (radius search, distance) in PostgreSQL |
| **Anonymous citizen token** | Citizens report without registration; token stored in `localStorage` |
| **ARRAY(String) for tags** | PostgreSQL native array for multi-label tag storage |
| **Enum for department** | Enforces valid department values at DB level |
| **priority_score column** | Pre-calculated score (votes + age + status) for fast sorting |

---

## Authentication & Authorization

```mermaid
flowchart LR
    subgraph "Public Endpoints"
        P1["POST /issues/\n(report issue)"]
        P2["GET /issues/\n(read feed)"]
        P3["GET /notifications/my-notifications\n(by token)"]
        P4["GET /analytics/*"]
    end

    subgraph "Auth Flow"
        LOGIN["POST /auth/login\n→ JWT token"]
    end

    subgraph "Protected — Any Authenticated User"
        A1["GET /auth/me"]
    end

    subgraph "Protected — Officials + Super Admin"
        B1["GET /admin/issues"]
        B2["GET /admin/stats"]
    end

    subgraph "Protected — Super Admin Only"
        C1["POST /auth/register"]
        C2["PATCH /admin/:id/reassign"]
        C3["DELETE /admin/:id"]
    end

    LOGIN -->|"Bearer JWT"| A1
    LOGIN -->|"Bearer JWT"| B1
    LOGIN -->|"Bearer JWT (super_admin)"| C1
```

**User Roles:**

| Role | Value | Capabilities |
|------|-------|-------------|
| `super_admin` | Super Admin | All operations: view all issues, reassign, delete, create users |
| `official` | Department Official | View & manage only their department's issues |

---

## Service Dependencies

```mermaid
graph TD
    BE[FastAPI App]
    
    BE -->|"TCP 5432"| PG[(PostgreSQL\n+ PostGIS)]
    BE -->|"HTTPS API"| CDN[Cloudinary]
    BE -->|"HTTPS API"| GEM[Google Gemini API]
    BE -->|"in-process\nshared memory"| CLIP[CLIP Model\nHuggingFace]
    BE -->|"file I/O\nfaiss_index.bin"| FAISS[Faiss Index]
    BE -->|"TCP 465 SMTP"| EMAIL[Gmail SMTP]

    CLIP -->|"downloads on first run"| HF[HuggingFace Hub]
```

### External Services Summary

| Service | Protocol | Config Variable | Required |
|---------|----------|----------------|---------|
| PostgreSQL | TCP 5432 | `DATABASE_URL` | ✅ Yes |
| Cloudinary | HTTPS | `CLOUDINARY_*` | ✅ Yes |
| Google Gemini | HTTPS | `GEMINI_API_KEY` | ✅ Yes |
| Gmail SMTP | SMTP/SSL | `SMTP_EMAIL`, `SMTP_PASSWORD` | ⚠️ Optional |

---

## Deployment Architecture

See [Deployment Guide](./deployment.md) for full setup instructions.

```mermaid
graph TB
    subgraph "Production"
        V["Vercel\nNext.js Frontend\nadvolens.vercel.app"]
        R["Render.com / VPS\nFastAPI Backend\n:8000"]
        DB["Cloud PostgreSQL\n+ PostGIS"]
        CDN2["Cloudinary\nImage CDN"]
    end

    subgraph "CI/CD"
        GHA["GitHub Actions\nbuild-and-push.yml"]
        DH["Docker Hub\nsanjanamsanthoshsct/advolens-backend"]
        WT["Watchtower\n(auto-deploy on VPS)"]
    end

    GHA -->|"push image"| DH
    DH -->|"auto-pull"| WT
    WT -->|"restart"| R
    V -->|"API calls"| R
    R -->|"SQL"| DB
    R -->|"upload"| CDN2
```
