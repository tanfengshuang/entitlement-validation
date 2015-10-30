import os
import json
import commands

# test data
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel6.7/rhel-6.7-beta-blacklist-prod.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel5.10/rhel5.10-rc-1.3.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel7.2/rhel-7.2-snapshot1-qa-cdn.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhcmsys8/15017-package-manifest.json

manifest_file = "manifest.properties"
MANIFEST_PATH = "MANIFEST.json"
MANIFEST_URL = open(manifest_file, 'r').read().split("\n")[0]

# check if there is MANIFEST.json, if yes, delete it and re-download
if os.path.exists(MANIFEST_PATH):
    commands.getstatusoutput("rm -rf %s" % MANIFEST_PATH)
    print "deleting MANIFEST.json"
cmd = 'wget %s -O %s' % (MANIFEST_URL, MANIFEST_PATH)
print cmd
ret, output1 = commands.getstatusoutput(cmd)
if ret == 0:
    print "download manifest successfully."

# open MANIFEST.json
content = json.load(open(MANIFEST_PATH, 'r'))

# parse MANIFEST.json to get test platforms
if "cdn" in content.keys():
    platforms = []
    cdn = content["cdn"]
    for pid in content["cdn"]["products"]:
        for repo_path in content["cdn"]["products"][pid]["Repo Paths"]:
            basearch = content["cdn"]["products"][pid]["Repo Paths"][repo_path]["basearch"]
            #releasever = content["cdn"]["products"][pid]["Repo Paths"][repo_path]["releasever"]
            variant = repo_path.split('/')[4]
            if variant == "server" or variant == "system-z" or variant == "power" or variant == "power-le" or variant == "arm":
                variant = "Server"
            if variant == "client":
                variant = "Client"
            if variant == "workstation":
                variant = "Workstation"
            if variant == "computenode":
                variant = "ComputeNode"
            platforms.append("{0}_{1}".format(variant, basearch))
    platforms = list(set(platforms))
    print "Need to do testing on:", platforms
    # ready to write testing properties files
    # ['Server_ppc64le', 'ComputeNode_x86_64', 'Server_aarch64', 'Server_ppc64', 'Client_x86_64', 'Server_s390x', 'Server_x86_64', 'Workstation_x86_64']
    for file in platforms:
        with open("{0}.properties".format(file), 'w') as f:
            f.write(file)
elif "rhn" in content.keys():
    pass
