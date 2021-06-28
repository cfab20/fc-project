output "cloud-server-public-ip" {
  value = google_compute_instance.cloud_instance.network_interface.0.access_config.0.nat_ip
}


#output "cloud-database-public-ip" {
#  value = google_sql_database_instance.instance.public_ip_address
#}

#output "cloud-database-public-ip" {
#  value = google_bigtable_instance.production-instance.public_ip_address
#}
