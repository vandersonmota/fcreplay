provider "google" {
  version = "3.5.0"

  credentials = file("<NAME>.json")

  project = "fcrecorder"
  region  = "us-central1"
  zone    = "us-central1-a"
}

