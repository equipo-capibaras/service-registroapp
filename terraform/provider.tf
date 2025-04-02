terraform {
  required_providers {
    google = {
      version = "~> 6.28.0"
    }
  }
}

# State is stored in a GCS bucket.
terraform {
  backend "gcs" {
    prefix = "service-registroapp/state"
  }
}

# Configures the Google Cloud Platform provider.
provider "google" {
  project = local.project_id
  region  = local.region
}
