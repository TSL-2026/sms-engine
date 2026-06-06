# ✈️ Aviation Safety System - Google Cloud Deployment Checklist
## Phase 2: Firestore Integration & Cloud Run Deployment

**Project:** Aviation Safety Intelligence System  
**Version:** v2.2 → v3.0 (Cloud Native)  
**Target Platform:** Google Cloud Platform (Blaze Plan)  

---

## 📊 PHASE 2: COMPLETE CHECKLIST

### ✅ Pre-Deployment Setup

#### 1. GCP Project Configuration
- [ ] Create/select GCP project
- [ ] Enable billing (Blaze plan)
- [ ] Set project ID: `aviation-safety-xxxxx`
- [ ] Install Google Cloud SDK (`gcloud` CLI)
- [ ] Login: `gcloud auth login`
- [ ] Set project: `gcloud config set project PROJECT_ID`

#### 2. Enable Required APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com