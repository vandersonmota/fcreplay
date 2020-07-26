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

//Add permissions to fcrecorder-compute-account cloud-functions
resource "google_project_iam_binding" "compute_admin" {
  project = "fcrecorder"
  role    = "roles/compute.admin"
  members = ["serviceAccount:fcrecorder-compute-account@fcrecorder.iam.gserviceaccount.com"]
}

resource "google_project_iam_binding" "functions_invoker" {
  project = "fcrecorder"
  role    = "roles/cloudfunctions.invoker"
  members = ["serviceAccount:fcrecorder-compute-account@fcrecorder.iam.gserviceaccount.com"]
}

// Add VNC Firewall rule
resource "google_compute_firewall" "incomming-vnc" {
  name    = "incomming-vnc"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["5900"]
  }

  source_tags = ["incomming-vnc"]
}

// Create chatbot instance
resource "google_compute_instance" "chatbot" {
  name         = "chatbot"
  machine_type = "f1-micro"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "centos-cloud/centos-7"
    }
  }

  network_interface {
    network = "default"

    access_config {
      // Ephemeral IP
    }
  }
}

// Create base image - Needs manual resize
resource "google_compute_instance" "default" {
  name         = "fcrecorder"
  machine_type = "n1-standard-4"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "projects/fcrecorder/global/images/fedora-32"
      size = "20"
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral IP
    }
  }

  tags = ["incomming-vnc"]
}

//Create cloud functions
resource "null_resource" "cloud_functions" {
  provisioner "local-exec" {
    command = "cd ./cloud_functions; ./deploy.sh"
  }
}

//Deploy scheduled tasks
resource "google_cloud_scheduler_job" "check_for_replay" {
  name             = "check_for_replay"
  description      = "Triggers cloud function to look for replays"
  schedule         = "*/2 * * * *"

  http_target {
    http_method = "GET"
    uri         = "https://us-central1-fcrecorder.cloudfunctions.net/check_for_replay"

    oidc_token {
      service_account_email = "fcrecorder-compute-account@fcrecorder.iam.gserviceaccount.com"
      audience = "https://us-central1-fcrecorder.cloudfunctions.net/check_for_replay"
    }
  }
}