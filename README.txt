SENSORS:

python3 device_emulator.py 


EDGE:

python3 edge.py 


CLOUD:

python3 cloud.py



# Deploy Infrastructure

During the creation and connection the key at "~/.ssh/id_rsa" will be used as the connection key

install gcloud sdk (https://cloud.google.com/sdk/docs/install#optional_install_the_latest_google_cloud_client_libraries)
configure it with "gcloud init"
and set it as the default login mechanism "gcloud auth application-default login"

configure the project id at top of the terraform main.tf
run "terraform apply"

At the end the public IP of the created cloud vm will be displayed.

ssh fogcomputing@public.ip

run "gcloud init" and "gcloud auth application-default login"

then clone the git repository with "git clone https://github.com/cfab20/fc-project.git"
cd fc-project
run "python3 cloud.py"
