import os

manifest_url = os.environ["Manifest_URL"]
variant = os.environ["Variant"]
arch = os.environ["Arch"]
rhn = os.environ["RHN"]

# rhn server url
server_url = {
    "QA": "https://xmlrpc.rhn.qa.redhat.com/XMLRPC",
    "Live": "https://xmlrpc.rhn.redhat.com/XMLRPC"
}

# accounts used for rhn testing
account_rhn = {
    "Live": {
        "username": "qa@redhat.com",
        "password": "QMdMJ8jvSWUwB6WZ"
    },
    "QA": {
        "username": "qa@redhat.com",
        "password": "redhatqa"
    }
}
