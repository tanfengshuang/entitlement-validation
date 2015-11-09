# testing parameters got from upstream trigger job
manifest_url = "MANIFEST_URL"
pid = "PID"
variant = "VARIANT"
arch = "ARCH"
cdn = "CDN"
rhn = "RHN"
candlepin = "CANDLEPIN"
beaker_ip = "BEAKER_IP"

# accounts used for testing
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

account_cdn_prod = {
    "username": "qa@redhat.com",
    "password": "",
    "sku": {
        "68": "",
        "69": "",
        "71": "",
        "72": "",
        "74": "",
        "76": "",
        "83": "",
        "90": "",
        "146": "",
        "241": "",
        "279": "",
        "287": "",
        "294": "",
        "299": "",
        "300": ""
    }
}

account_cdn_stage = {
    "68": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "69": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "71": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "72": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "74": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "76": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "83": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "90": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "146": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "241": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "279": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "287": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "294": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "299": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    },
    "300": {
        "username": "",
        "password": "redhat",
        "SKU": ""
    }
}
