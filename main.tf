provider "google" {
  version = "3.5.0"

  credentials = file("~/.fcrecorder-api-credentials.json")

  project = "fcrecorder"
  region  = "us-central1"
  zone    = "us-central1-a"
}

resource "google_service_account" "fcrecorder_compute_account" {
  account_id   = "fcrecorder-compute-account"
  display_name = "FCRecorder compute account"
}

//Add permissions to fcrecorder-compute-account
resource "google_project_iam_binding" "project" {
  project = "fcrecorder"
  role    = "roles/compute.admin"
  members = ["serviceAccount:fcrecorder-compute-account@fcrecorder.iam.gserviceaccount.com"]
}

