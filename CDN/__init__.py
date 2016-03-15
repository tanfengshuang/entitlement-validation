import os

manifest_url = os.environ["Manifest_URL"]
variant = os.environ["Variant"]
arch = os.environ["Arch"]
cdn = os.environ["CDN"]
test_level = os.environ["Test_Level"]
release_ver = os.environ["Release_Version"]
candlepin = os.environ["Candlepin"]


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


# Account info
stage_username = "entitlement_testing"
stage_password = "redhat"
prod_username = "qa@redhat.com"
prod_password = "a85xH8a5w8EaZbdS"

account_info = {
    "68": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "MCT0474",
            "base_sku": "MCT0474"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "68",
        "product_name": "Red Hat Enterprise Linux Desktop"
    },
    "69": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "RH0103708",
            "base_sku": "RH0103708"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "69",
        "product_name": "Red Hat Enterprise Linux Server"
    },
    "71": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "MCT0351",
            "base_sku": "MCT0351"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "71",
        "product_name": "Red Hat Enterprise Linux Workstation"
    },
    "72": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "MCT0343",
            "base_sku": "MCT0343"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "72",
        "product_name": "Red Hat Enterprise Linux for IBM z Systems"
    },
    "74": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "MCT0984",
            "base_sku": "MCT0984"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "74",
        "product_name": "Red Hat Enterprise Linux for Power, big endian"
    },
    "76": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "MCT0978",
            "base_sku": "MCT0978"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "76",
        "product_name": "Red Hat Enterprise Linux for Scientific Computing"
    },
    "83": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "MCT0367",
            "base_sku": "RH0103708"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "69",
        "product_name": "Red Hat Enterprise Linux High Availability (for RHEL Server)"
    },
    "85": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "RH00028",
            "base_sku": "RH0103708"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "69",
        "product_name": "Red Hat Enterprise Linux Load Balancer (for RHEL Server)"
    },
    "90": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "MCT0456",
            "base_sku": "RH0103708"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "69",
        "product_name": "Red Hat Enterprise Linux Resilient Storage (for RHEL Server)"
    },
    "92": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "MCT1761",
            "base_sku": "RH0103708"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "69",
        "product_name": "Red Hat Enterprise Linux Scalable File System (for RHEL Server)"
    },
    "94": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "RH00027",
            "base_sku": "MCT0351"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "71",
        "product_name": "Red Hat Enterprise Linux Scalable File System (for RHEL Workstation)"
    },
    "135": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "135",
        "product_name": ""
    },
    "155": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "155",
        "product_name": ""
    },
    "146": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "MCT1731",
            "base_sku": "RH0103708"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "69",
        "product_name": "Red Hat Enterprise Linux for SAP"
    },
    "175": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "MCT2011",
            "base_sku": "MCT0978"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "76",
        "product_name": "Red Hat Enterprise Linux Scalable File System (for RHEL Compute Node)"
    },
    "241": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "RH00196",
            "base_sku": "RH0103708"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "69",
        "product_name": "Red Hat Enterprise Linux for SAP Hana"
    },
    "279": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "RH00284",
            "base_sku": "RH00284"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "279",
        "product_name": "Red Hat Enterprise Linux for Power, little endian"
    },
    "287": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "RH00428",
            "base_sku": "RH00428"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "69",
        "product_name": "Red Hat Enterprise Linux for Real Time"
    },
    "294": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "MCT3115",
            "base_sku": "MCT3115"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "294",
        "product_name": "Red Hat Enterprise Linux Server for ARM"
    },
    "299": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "RH00545",
            "base_sku": "MCT0343"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "72",
        "product_name": "Red Hat Enterprise Linux Resilient Storage (for IBM z Systems)"
    },
    "300": {
        "Stage": {
            "username": stage_username,
            "password": stage_password,
            "sku": "RH00546",
            "base_sku": "MCT0343"
        },
        "Prod": {
            "username": prod_username,
            "password": prod_password,
            "sku": "ES0113909",
            "base_sku": "ES0113909"
        },
        "base_pid": "72",
        "product_name": "Red Hat Enterprise Linux High Availability (for IBM z Systems)"
    }
}
