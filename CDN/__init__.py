import os

manifest_url = os.environ["Manifest_URL"]
variant = os.environ["Variant"]
arch = os.environ["Arch"]
cdn = os.environ["CDN"]
test_level = os.environ["Test_Level"]
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


# RHEL Variant:
# 68  client
# 69  server-x86_64
# 71  workstation
# 72  server-s390x
# 74  server-ppc64
# 76  computenode-x86_64
# 135 server-x86_64         - RHEL6 HTB
# 155 workstation-x86_64    - RHEL6 HTB
# 279 server-ppc64le    - RHEL7
# 294 server-aarch64    - RHEL7
base_repo = {
    "6": {
        "Beta": {
            "68": "rhel-6-desktop-beta-rpms",
            "69": "rhel-6-server-beta-rpms",
            "71": "rhel-6-workstation-beta-rpms",
            "72": "rhel-6-for-system-z-beta-rpms",
            "74": "rhel-6-for-power-beta-rpms",
            "76": "rhel-6-hpc-node-beta-rpms"
            },
        "GA": {
            "68": "rhel-6-desktop-rpms",
            "69": "rhel-6-server-rpms",
            "71": "rhel-6-workstation-rpms",
            "72": "rhel-6-for-system-z-rpms",
            "74": "rhel-6-for-power-rpms",
            "76": "rhel-6-hpc-node-rpms"
        },
        "HTB": {
            "135": "rhel-6-server-htb-rpms",
            "155": "rhel-6-workstation-htb-rpms"
        }
    },
    "7": {
        "Beta": {
            "68": "rhel-7-desktop-beta-rpms",
            "69": "rhel-7-server-beta-rpms",
            "71": "rhel-7-workstation-beta-rpms",
            "72": "rhel-7-for-system-z-beta-rpms",
            "74": "rhel-7-for-power-beta-rpms",
            "76": "rhel-7-hpc-node-beta-rpms",
            "279": "rhel-7-for-power-le-beta-rpms",
            "294": "rhel-7-for-arm-beta-rpms"
        },
        "GA": {
            "68": "rhel-7-desktop-rpms",
            "69": "rhel-7-server-rpms",
            "71": "rhel-7-workstation-rpms",
            "72": "rhel-7-for-system-z-rpms",
            "74": "rhel-7-for-power-rpms",
            "76": "rhel-7-hpc-node-rpms",
            "279": "rhel-7-for-power-le-rpms",
            "294": "rhel-7-for-arm-rpms"
        }
    }
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
    "85": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "90": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "92": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "135": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "135"
    },
    "155": {
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "155"
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
    "85": {
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
    "92": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "69"
    },
    "135": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "135"
    },
    "155": {
        "username": "entitlement_testing",
        "password": "redhat",
        "sku": "ES0113909",
        "base_sku": "ES0113909",
        "base_pid": "155"
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

