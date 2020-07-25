provider "google" {
  version = "3.5.0"

  credentials = file("~/.fcrecorder-api-credentials.json")

  project = "fcrecorder"
  region  = "us-central1"
  zone    = "us-central1-a"
}


//Create service accounts
resource "google_service_account" "fcrecorder-storage-access" {
  account_id   = "fcrecorder-storage-access"
  display_name = "FCRecorder storage account"
}

resource "google_service_account" "fcrecorder-compute-account" {
  account_id   = "fcrecorder-compute-account"
  display_name = "FCRecorder compute account"
}

//Add permissions to fcrecorder-compute-account
resource "google_project_iam_policy" "project" {
  project     = "fcrecorder"
  policy_data = data.google_iam_policy.compute_admin.policy_data
  depends_on  = [google_service_account.fcrecorder-compute-account]
}

data "google_iam_policy" "compute_admin" {
  binding {
    role = "roles/compute.admin`"
    members = ["serviceAccount:fcrecorder-compute-account@fcrecorder.iam.gserviceaccount.com"]
  }
}

/*Add permissions to fcrecorder-storage-access
resource "google_project_iam_policy" "project-storage" {
  project     = "fcrecorder"
  policy_data = data.google_iam_policy.storage_admin.policy_data
  depends_on = [google_service_account.fcrecorder-storage-access]
}

data "google_iam_policy" "storage_admin" {
  binding {
    role = "roles/roles/storage.admin"
    members = [
      "user:fcrecorder-storage-access@fcrecorder.iam.gserviceaccount.com",
    ]
  }
}
*/

resource "null_resource" "get_storage_key" {
  provisioner "local-exec" {
    command = "gcloud iam service-accounts keys create .storage_creds.json --iam-account fcrecorder-storage-access@fcrecorder.iam.gserviceaccount.com"
  }
  depends_on = [google_service_account.fcrecorder-storage-access]
}