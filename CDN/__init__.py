import os

manifest_url = os.environ["MANIFEST_URL"]
pid = os.environ["PID"]
variant = os.environ["VARIANT"]
arch = os.environ["ARCH"]
cdn = os.environ["CDN"]
blacklist = os.environ["BLACKLIST"]
release_ver = os.environ["RELEASE_VERSION"]
candlepin = os.environ["CANDLEPIN"]
beaker_ip = os.environ["BEAKER_IP"]

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
        "sku": "",
        "base_sku": "",
        "base_pid": "68"
    },
    "69": {
        "sku": "",
        "base_sku": "",
        "base_pid": "69"
    },
    "71": {
        "sku": "",
        "base_sku": "",
        "base_pid": "71"
    },
    "72": {
        "sku": "",
        "base_sku": "",
        "base_pid": "72"
    },
    "74": {
        "sku": "",
        "base_sku": "",
        "base_pid": "74"
    },
    "76": {
        "sku": "",
        "base_sku": "",
        "base_pid": "76"
    },
    "83": {
        "sku": "",
        "base_sku": "",
        "base_pid": "69"
    },
    "90": {
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "146": {
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "241": {
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "279": {
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "287": {
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "294": {
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "299": {
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "300": {
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    }
}

account_cdn_stage = {
    "68": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": "68"
    },
    "69": {
        "username": "stage_test_12",
        "password": "redhat",
        "sku": "RH0103708",
        "base_sku": "RH0103708",
        "base_pid": "69"
    },
    "71": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": "71"
    },
    "72": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": "72"
    },
    "74": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": "74"
    },
    "76": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": "76"
    },
    "83": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": "69"
    },
    "90": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "146": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "241": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "279": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "287": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "294": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "299": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    },
    "300": {
        "username": "",
        "password": "redhat",
        "sku": "",
        "base_sku": "",
        "base_pid": ""
    }
}

