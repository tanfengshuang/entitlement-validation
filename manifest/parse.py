import os
import json
import commands

# test data
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel6.7/rhel-6.7-beta-blacklist-prod.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel5.10/rhel5.10-rc-1.3.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel7.2/rhel-7.2-snapshot1-qa-cdn.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhcmsys8/15017-package-manifest.json

pid_file = "pid.txt"
variant_file = "variant.txt"
baseinfo_file = "baseinfo.txt"
manifest_file = "manifest.txt"
MANIFEST_PATH = "MANIFEST.json"
MANIFEST_URL = open(manifest_file, 'r').read().split("\n")[0]


def generate_properties(variant_arch, pid):
    variant = variant_arch.split("-")[0]
    arch = variant_arch.split("-")[1]
    file_name = "{0}.properties".format(variant_arch)
    if os.path.exists(file_name):
        with open(file_name, 'a+') as f:
            f.write("PID={0}\n".format(pid))
            print "write PID {0} into {1}.properties".format(pid, variant_arch)
    else:
        with open(file_name, 'a+') as f:
            f.write("VARIANT={0}\n".format(variant))
            f.write("ARCH={0}\n".format(arch))
            f.write("PID={0}\n".format(pid))
            print "write variant({0}), arch({1}) and pid({2}) into {3}.properties".format(variant, arch, pid, variant_arch)

def download_manifest():
    # check if there is MANIFEST.json, if yes, delete it and re-download
    if os.path.exists(MANIFEST_PATH):
        commands.getstatusoutput("rm -rf %s" % MANIFEST_PATH)
        print "deleting MANIFEST.json"
    cmd = 'wget %s -O %s' % (MANIFEST_URL, MANIFEST_PATH)
    print cmd
    ret, output = commands.getstatusoutput(cmd)
    if ret == 0:
        print "download manifest successfully."
    else:
        print "Failed to download manifest!"
        exit(1)

def get_pid_variant():
    PIDs = ""
    VARIANTs = ""
    if os.path.exists(pid_file):
        with open("{0}".format(pid_file), 'r') as f:
            PIDs = f.read().split('\n')[0]
    if os.path.exists(variant_file):
        with open("{0}".format(variant_file), 'r') as f:
            VARIANTs = f.read().split('\n')[0]
    return PIDs, VARIANTs

def check_arches(VARIANTs, PIDs):
    variants = []
    for v in VARIANTs.split(","):
        if v in PIDs:
            variants.append(v)
        else:
            print "Warning: variant {0} is not in manifest!".format(v)
    return variants

def parse_cdn():
    download_manifest()

    # read PID and VARIANT from jenkins parameters
    PIDs, VARIANTs = get_pid_variant()

    # open and read MANIFEST.json
    content = json.load(open(MANIFEST_PATH, 'r'))

    # parse MANIFEST.json to get test platforms
    platforms = {}
    if "cdn" in content.keys():
        for pid in content["cdn"]["products"]:
            arches = []
            for repo_path in content["cdn"]["products"][pid]["Repo Paths"]:
                basearch = content["cdn"]["products"][pid]["Repo Paths"][repo_path]["basearch"]
                variant = repo_path.split('/')[4]
                if variant in ["server", "system-z", "power", "power-le", "arm"]:
                    variant = "Server"
                if variant == "client":
                    variant = "Client"
                if variant == "workstation":
                    variant = "Workstation"
                if variant == "computenode":
                    variant = "ComputeNode"
                # arches: ['Server-ppc64le', 'ComputeNode-x86_64', 'Server-aarch64', 'Server-ppc64', 'Client-x86_64', 'Server-s390x', 'Server-x86_64', 'Workstation-x86_64']
                arches.append("{0}-{1}".format(variant, basearch))
                platforms[pid] = list(set(arches))
        # platforms format: {"68":["Client-x86_64", "Client-i386"], "69":["Server-X86_64", "Server-i386"]}
        print "PID, Variants and arches list in manifest:"
        for i in platforms:
            print "{0}: {1}".format(i, platforms[i])

        if PIDs == "" and VARIANTs == "":
            # ready to write testing properties files
            # *.properties file content
            # MANIFEST_URL=http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel6.7/rhel-6.7-beta-blacklist-prod.json
            # DISTRO=RHEL-7.2-20150904.0
            # CDN=QA
            # CANDLEPIN=Stage
            # VARIANT=Server
            # ARCH=i386
            for pid in platforms:
                # generate *.properties files used to trigger downstream jobs
                for variant_arch in platforms[pid]:
                    generate_properties(variant_arch, pid)
        elif PIDs != "":
            for pid in PIDs.split(","):
                if pid not in platforms.keys():
                    print "Warning: PID {0} is not in manifest!".format(pid)
                    continue
                if VARIANTs == "":
                    # generate *.properties files used to trigger downstream jobs
                    for variant_arch in platforms[pid]:
                        generate_properties(variant_arch, pid)
                else:
                    # Delete those invalid arches which are not in manifest
                    variants = check_arches(VARIANTs, platforms[pid])
                    # generate *.properties files used to trigger downstream jobs
                    for variant_arch in variants:
                        generate_properties(variant_arch, pid)
        else:
            # Delete those invalid arches which are not in manifest
            variants = check_arches(VARIANTs, platforms[pid])
            # generate *.properties files used to trigger downstream jobs
            for variant_arch in variants:
                generate_properties(variant_arch, pid)

        # copy the content of file $baseinfo_file to *.properties
        ret, output = commands.getstatusoutput("ls | grep properties")
        if output != "":
            for file in output.split("\n"):
                output = commands.getoutput("cat %s | grep PID | awk -F'=' '{print $2}'" % file)
                if output != "":
                    # merge several PIDs into one line, such as, merge the following lines to PID=90,83,69
                    # PID=90
                    # PID=83
                    # PID=69
                    content = "cat {0} | grep -v PID".format(file)
                    #tmp_file = "{0}.bk".format(file)
                    #os.rename(file, "{0}".format(tmp_file))
                    PID_info = output.replace('\n', ',')
                    with open("{0}".format(file), 'w') as f1:
                        #f1.write(commands.getoutput("cat {0} | grep -v PID".format(tmp_file)))
                        f1.write(content)
                        f1.write("\nPID={0}\n".format(PID_info))
                with open("{0}".format(file), 'a+') as f1:
                    # write $baseinfo_file content to *.properties
                    with open("{0}".format(baseinfo_file), 'r') as f2:
                        base_info = f2.read()
                        f1.write(base_info)


def pasee_rhn():
    download_manifest()

    # read PID and VARIANT from jenkins parameters
    PIDs, VARIANTs = get_pid_variant()

    # open and read MANIFEST.json
    content = json.load(open(MANIFEST_PATH, 'r'))

    if "rhn" in content.keys():
        pass

if __name__ == '__main__':
    parse_cdn()

