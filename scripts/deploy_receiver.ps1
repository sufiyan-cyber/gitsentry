# =============================================================================
# GitSentry - Cloud Run Deployment Script for PowerShell (Windows)
# =============================================================================

$ErrorActionPreference = "Continue"

$ProjectId = $env:GCP_PROJECT_ID
if (-not $ProjectId) {
    $ProjectId = (gcloud config get-value project 2>$null).Trim()
}

$Region = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$ServiceName = "gitsentry-webhook-receiver"
$TopicName = "pr-events"
$RepoName = "gitsentry"
$ImageName = "${Region}-docker.pkg.dev/${ProjectId}/${RepoName}/${ServiceName}:latest"

Write-Host "================================================================="
Write-Host " Deploying GitSentry Webhook Receiver to Google Cloud Run"
Write-Host " Project ID:  $ProjectId"
Write-Host " Region:      $Region"
Write-Host " Service:     $ServiceName"
Write-Host " Image:       $ImageName"
Write-Host "================================================================="

# 1. Enable Required GCP APIs
Write-Host ""
Write-Host "--> 1/5 Enabling GCP APIs..."
gcloud services enable `
    run.googleapis.com `
    secretmanager.googleapis.com `
    pubsub.googleapis.com `
    firestore.googleapis.com `
    aiplatform.googleapis.com `
    cloudbuild.googleapis.com `
    artifactregistry.googleapis.com `
    --project=$ProjectId
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR enabling APIs"; exit 1 }

# 2. Create Artifact Registry Docker repo if not exists
Write-Host ""
Write-Host "--> 2/5 Creating Artifact Registry repo..."
gcloud artifacts repositories describe $RepoName --location=$Region --project=$ProjectId 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Repo not found. Creating..."
    gcloud artifacts repositories create $RepoName `
        --repository-format=docker `
        --location=$Region `
        --project=$ProjectId `
        --description="GitSentry container images"
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR creating Artifact Registry repo"; exit 1 }
    Write-Host "Created Artifact Registry repo."
} else {
    Write-Host "Artifact Registry repo already exists."
}

# Grant Cloud Build service account permission to push images
Write-Host "Granting Artifact Registry push permissions..."
$ProjectNumber = (gcloud projects describe $ProjectId --format="value(projectNumber)" 2>$null).Trim()
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:${ProjectNumber}-compute@developer.gserviceaccount.com" `
    --role="roles/artifactregistry.writer" `
    --quiet 2>$null | Out-Null
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:${ProjectNumber}-compute@developer.gserviceaccount.com" `
    --role="roles/logging.logWriter" `
    --quiet 2>$null | Out-Null
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:${ProjectNumber}-compute@developer.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor" `
    --quiet 2>$null | Out-Null
Write-Host "Permissions granted."

# 3. Create Pub/Sub Topic if not exists
Write-Host ""
Write-Host "--> 3/5 Verifying Pub/Sub Topic..."
gcloud pubsub topics describe $TopicName --project=$ProjectId 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating Pub/Sub topic $TopicName..."
    gcloud pubsub topics create $TopicName --project=$ProjectId
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR creating topic"; exit 1 }
} else {
    Write-Host "Topic already exists."
}

# 4. Build Container Image via Google Cloud Build
Write-Host ""
Write-Host "--> 4/5 Building container image with Cloud Build..."
Write-Host "    This uploads code to GCP and builds Docker image remotely (2-3 min)."
gcloud builds submit `
    --tag $ImageName `
    --project=$ProjectId `
    .
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Cloud Build failed. Check the build logs above."
    exit 1
}
Write-Host "Image built and pushed successfully."

# 5. Deploy to Cloud Run
Write-Host ""
Write-Host "--> 5/5 Deploying service to Cloud Run..."
gcloud run deploy $ServiceName `
    --image=$ImageName `
    --region=$Region `
    --platform=managed `
    --allow-unauthenticated `
    --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=$ProjectId,PUBSUB_TOPIC_PR_EVENTS=$TopicName" `
    --set-secrets="GITHUB_WEBHOOK_SECRET=github-webhook-secret:latest" `
    --min-instances=0 `
    --max-instances=10 `
    --memory=512Mi `
    --cpu=1 `
    --project=$ProjectId
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Cloud Run deployment failed."
    exit 1
}

$ReceiverUrl = (gcloud run services describe $ServiceName --platform=managed --region=$Region --project=$ProjectId --format='value(status.url)' 2>$null).Trim()

Write-Host ""
Write-Host "================================================================="
Write-Host " GitSentry Webhook Receiver Successfully Deployed!"
Write-Host " Webhook URL: $ReceiverUrl/webhook"
Write-Host ""
Write-Host " Paste this URL into your GitHub App Webhook settings."
Write-Host "================================================================="
Write-Host ""
