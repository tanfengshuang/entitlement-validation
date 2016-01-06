import os

manifest_url = os.environ["Manifest_URL"]
variant = os.environ["Variant"]
arch = os.environ["Arch"]
sat5_server = os.environ["SAT5_Server"]


# accounts used for SAT5 testing
sat5_account = {
    "username": "admin",
    "password": "nimda"
}