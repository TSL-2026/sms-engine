#!/bin/bash
# Complete GitHub setup for SMS-Engine

set -e

echo "🚀 Setting up GitHub CI/CD for SMS-Engine"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI not found. Installing...${NC}"
    brew install gh
fi

# Authenticate with GitHub
echo -e "${GREEN}Authenticating with GitHub...${NC}"
gh auth login

# Create repository
echo -e "${GREEN}Creating GitHub repository...${NC}"
gh repo create sms-engine --public --description "Aviation Safety Intelligence System - ICAO-aligned risk assessment with AI explanations" --source=. --remote=origin --push

# Create service account for CI/CD
PROJECT_ID=$(gcloud config get-value project)
echo -e "${GREEN}Creating service account for CI/CD in project: $PROJECT_ID${NC}"

gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions CI/CD" \
  --project=$PROJECT_ID 2>/dev/null || echo "Service account already exists"

# Grant roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"

# Create and save key
KEY_FILE="/tmp/github-actions-key-$(date +%s).json"
gcloud iam service-accounts keys create $KEY_FILE \
  --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com

# Add secrets to GitHub
echo -e "${GREEN}Adding secrets to GitHub repository...${NC}"

gh secret set GCP_SA_KEY < $KEY_FILE

IAP_CLIENT_ID="660696925387-rk1ffklc4bcje0toq2psnqf3kv24ujdn.apps.googleusercontent.com"
echo $IAP_CLIENT_ID | gh secret set IAP_CLIENT_ID

# Clean up
rm $KEY_FILE

echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "\n${GREEN}Next steps:${NC}"
echo "1. Push any additional changes: git push origin main"
echo "2. View workflows: https://github.com/$(gh repo view --json name -q .nameWithOwner)/actions"
echo "3. Your SMS-Engine will now auto-deploy on every push to main"
