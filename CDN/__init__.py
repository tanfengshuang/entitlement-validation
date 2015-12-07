import os

manifest_url = os.environ["Manifest_URL"]
variant = os.environ["VARIANT"]
arch = os.environ["ARCH"]
cdn = os.environ["CDN"]
blacklist = os.environ["Blacklist"]
release_ver = os.environ["Release_Version"]
candlepin = os.environ["Candlepin"]
beaker_ip = os.environ["Beaker_IP"]

# baseurl hostname server_url
cdn_baseurl = {
    "QA": "https://cdn.qa.redhat.com",
    "Prod": "https://cdn.redhat.com"
}

candlepin_hostname = {
    "Stage": "subscription.rhn.redhat.com",
    "Prod": "subscription.rhn.stage.redhat.com"
}

# accounts used for cdn testing
account_cdn_prod = {
    "username": "qa@redhat.com",
    "password": "QMdMJ8jvSWUwB6WZ",
    "68": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "68"
    },
    "69": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "71": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "71"
    },
    "72": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "72"
    },
    "74": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "74"
    },
    "76": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "76"
    },
    "83": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "90": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "146": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "241": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "279": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "279"
    },
    "287": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "294": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "294"
    },
    "299": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "72"
    },
    "300": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "72"
    }
}

account_cdn_stage = {
    "68": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "68"
    },
    "69": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "71": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "71"
    },
    "72": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "72"
    },
    "74": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "74"
    },
    "76": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "76"
    },
    "83": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "90": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "146": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "241": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "279": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "279"
    },
    "287": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "294": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "294"
    },
    "299": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "72"
    },
    "300": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "72"
    }
}

