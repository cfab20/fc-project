provider "google" {
  project = "adsp-302713"
  region  = "europe-west3"
  zone    = "europe-west3-a"
}

resource "random_id" "id" {
  byte_length = 4
}


resource "google_compute_instance" "cloud_instance" {
  name         = "cloud-server"
  machine_type = "n2-standard-2"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-10"
    }
  }

  network_interface {
    # A default network is created for all GCP projects
    network = google_compute_network.vpc_network.self_link
    access_config {
    }
  }
  metadata = {
    ssh-keys = "fogcomputing:${file("~/.ssh/id_rsa.pub")}"
  }
  
  local-exec { 
    interpreter = ["/bin/bash" ,"-c"],
    command = <<-EOT
      exec "sudo apt update && sudo apt upgrade -y"
      exec "sudo apt install git python3-pip python3-zmq apt-transport-https ca-certificates gnupg -y"
      exec "pip3 install google-cloud-bigtable==2.0.0"
      exec "echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list"
      exec "curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -"
      exec "sudo apt-get update && sudo apt-get install google-cloud-sdk"
      exec "sudo apt-get install google-cloud-sdk-app-engine-java"
    EOT
  }
}


resource "google_compute_network" "vpc_network" {
  name                    = "cloud-network"
  auto_create_subnetworks = "true"
}
#################################################################
#            Database
#################################################################

resource "google_bigtable_instance" "production-instance" {
  name = "tf-instance"
  deletion_protection=false
  cluster {
    cluster_id   = "tf-instance-cluster"
    num_nodes    = 1
    storage_type = "HDD"
  }

  labels = {
    my-label = "prod-label"
  }
}


#resource "google_sql_database" "database" {
#  name     = "cloud-database"
#  instance = google_sql_database_instance.instance.name
#}

#resource "google_sql_database_instance" "instance" {
#  name   = "cloud-database-instance"
#  region = "europe-west3"
#  database_version = "POSTGRES_11"
#  deletion_protection = false
#  settings {
#    tier = "db-f1-micro"
#    ip_configuration {
#      ipv4_enabled    = true
#    }
#  }
#}


#################################################################
#            Firewall
#################################################################

resource "google_compute_firewall" "allow_ssh" {
  name = "cloud-network-internal-allow-ssh-${random_id.id.hex}"
  network = google_compute_network.vpc_network.self_link

  allow {
    protocol = "tcp"
    ports = ["22"]
  }
  source_ranges = ["0.0.0.0/0"]
}
resource "google_compute_firewall" "allow_internet" {
  name = "cloud-network-internal-allow-internet-${random_id.id.hex}"
  network = google_compute_network.vpc_network.self_link

  allow {
    protocol = "tcp"
    ports = ["80", "443"]
  }
  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "allow_zmq" {
  name = "cloud-network-internal-allow-zmq-${random_id.id.hex}"
  network = google_compute_network.vpc_network.self_link

  allow {
    protocol = "tcp"
    ports = ["5556"]
  }
  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "allow_zmq_heartbeat" {
  name = "cloud-network-internal-allow-zmq-heartbeat${random_id.id.hex}"
  network = google_compute_network.vpc_network.self_link

  allow {
    protocol = "tcp"
    ports = ["5557"]
  }
  source_ranges = ["0.0.0.0/0"]
}
