import os

manifest_url = os.environ["MANIFEST_URL"]
variant = os.environ["VARIANT"]
arch = os.environ["ARCH"]
rhn = os.environ["RHN"]
candlepin = os.environ["CANDLEPIN"]
beaker_ip = os.environ["BEAKER_IP"]

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
