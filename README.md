# AdvoLens: Civic Problem Solving Platform

**A Community-Driven Approach for Civic Problem Solving and Feedback**

## 📋 Project Overview

AdvoLens is an AI-powered platform that enables citizens to report civic issues (garbage, damaged roads, broken streetlights, clogged drains) through image-based submissions. The platform uses computer vision and machine learning to automatically analyze, categorize, and route issues to relevant authorities while preventing duplicate reports.

## 👥 Team Members

- **Sanjana M Santhosh** (SCT22AM054) - Backend Development, Database, ML Pipeline Integration
- **Aadinarayan M** (SCT22AM001) - Frontend Development, Dataset Creation, Optimization
- **Gowri A** (SCT22AM032) - ML Services (BLIP-2, Gemini), Admin Portal, Deployment

**Guide:** Kutty Malu V K, Assistant Professor, CSE Department  
**Institution:** Sree Chitra Thirunal College of Engineering

## 🎯 Problem Statement

Urban areas face recurring civic issues that remain unresolved due to:
- Delays in reporting
- Lack of coordination between citizens and authorities
- Duplicate reports overwhelming the system
- Inefficient resource allocation

## 💡 Our Solution

AdvoLens transforms civic issue reporting through:
- **Image-based reporting** with automatic GPS tagging
- **AI-powered analysis** using CLIP, BLIP-2, and Gemini
- **Duplicate detection** using Faiss vector similarity search
- **Geo-clustering** to identify problem hotspots
- **Real-time tracking** and status updates
- **Admin dashboard** for municipal authorities

## 🛠️ Tech Stack

### Frontend
- React.js / Next.js (Progressive Web App)
- Material-UI
- Mapbox/Google Maps API
- Axios

### Backend
- FastAPI (Python)
- PostgreSQL with PostGIS
- JWT Authentication
- SQLAlchemy

### AI/ML Services
- **CLIP** (OpenAI) - Image embeddings
- **BLIP-2** (Salesforce) - Image captioning
- **Faiss** - Vector similarity search (HNSW algorithm)
- **Gemini API** - Zero-shot classification & tagging
- **DBSCAN** - Geo-clustering

### Infrastructure
- Docker
- Google Cloud Run
- Google Cloud SQL
- Firebase Cloud Messaging (notifications)


## 🚀 Key Features

1. **Citizen App**
   - Report issues with photo + GPS
   - Track issue status in real-time
   - View community feed and map
   - Receive push notifications

2. **AI Analysis**
   - Automatic image captioning
   - Multi-label tagging
   - Visual duplicate detection
   - Spatial clustering

3. **Admin Dashboard**
   - Review and manage issues
   - Update status and assign departments
   - View analytics and hotspots
   - Filter by location/category/status


## 🔗 Links

- **GitHub Repository:** [Link]
- **Live Demo:** [Coming Soon]
- **Project Documentation:** [docs/](./docs/)
- **API Documentation:** [docs/api.md](./docs/api.md)

## 📝 License

This is an academic project for educational purposes.

## 📞 Contact

For questions or collaboration, reach out to the team members through GitHub issues.




