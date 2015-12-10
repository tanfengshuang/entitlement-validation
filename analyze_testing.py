import os
import sys
import json
import commands

# CDN test data
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel6.7/rhel-6.7-beta-blacklist-prod.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel5.10/rhel5.10-rc-1.3.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel7.2/rhel-7.2-snapshot1-qa-cdn.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhcmsys8/15017-package-manifest.json

# RHN test data
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel5.10/rhel5.10-rc-1.3.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhcmsys8/15017-package-manifest.json


def usage():
    print "Usage: {0} cdn|CDN|rhn|RHN|sat|SAT".format(sys.argv[0])
    exit(1)

def download_read_manifest(MANIFEST_PATH, MANIFEST_NAME, MANIFEST_URL):
    # Check if there is MANIFEST.json, if yes, delete it and re-download
    if os.path.exists(MANIFEST_PATH):
        if os.path.exists(MANIFEST_NAME):
            os.remove(MANIFEST_NAME)
            print "Deleting {0}".format(MANIFEST_NAME)
    else:
        os.mkdir(MANIFEST_PATH)
    cmd = 'wget %s -O %s' % (MANIFEST_URL, MANIFEST_NAME)
    print cmd
    ret, output = commands.getstatusoutput(cmd)
    if ret == 0:
        print "download manifest successfully."
    else:
        print "Failed to download manifest!"
        exit(1)

    # Open and load MANIFEST.json
    content = json.load(open(MANIFEST_PATH, 'r'))
    return content


class AnalyzeCDN(object):
    """
    1. Get base testing platforms from manifest, such as {"68":["Client-x86_64", "Client-i386"], "69":["Server-x86_64", "Server-i386"]}
    2. Get Jenkins upstream job parameter 'Product_ID' as PIDs and 'RHEL_Variant' as VARIANTs
    3. Get testing platform intersection
        If 'Product_ID' and 'RHEL_Variant' are both empty
        If 'Product_ID' is not empty, 'RHEL_Variant' is empty
        If 'Product_ID' is not empty, 'RHEL_Variant' is not empty
        If 'Product_ID' is empty, 'RHEL_Variant' is not empty
    4. Generate properties files(such as Server-x86_64.properties, Server-i386.properties), and write VARIANT, ARCH, PID variables
    5. Append other parameters into properties files in order to pass down these params listed in properties files to downstream jobs
    6. Content of properties file:
        VARIANT=Server
        ARCH=i386
        PID=90,83,69
        MANIFEST_URL=http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel6.7/rhel-6.7-beta-blacklist-prod.json
        DISTRO=RHEL-7.2-20150904.0
        CDN=QA
        CANDLEPIN=Stage
        BLACKLIST=GA
        RELEASE_VERSION=7.2
    """
    def __init__(self):
        # Get Jenkins job parameters
        self.DISTRO = os.environ["Distro"]
        self.CDN = os.environ["CDN"]
        self.CANDLEPIN = os.environ["Candlepin"]
        self.BLACKLIST = os.environ["Blacklist"]
        self.RELEASE_VERSION = os.environ["Release_Version"]
        self.PIDs = os.environ["Product_ID"]
        self.VARIANTs = os.environ["RHEL_Variant"]
        self.MANIFEST_URL = os.environ["Manifest_URL"]

        # Download and load manifest
        self.MANIFEST_PATH = os.path.join(os.getcwd(), "manifest")
        self.MANIFEST_NAME = os.path.join(self.MANIFEST_PATH, "CDN_MANIFEST.json")
        self.content = download_read_manifest(self.MANIFEST_PATH, self.MANIFEST_NAME, self.MANIFEST_URL)

    def analyze_cdn(self):
        if "cdn" in self.content.keys():
            # Get testing platforms from provided mainfest
            platforms = {}
            for pid in self.content["cdn"]["products"]:
                arches = []
                for repo_path in self.content["cdn"]["products"][pid]["Repo Paths"]:
                    basearch = self.content["cdn"]["products"][pid]["Repo Paths"][repo_path]["basearch"]
                    variant = repo_path.split('/')[4]
                    if variant in ["server", "system-z", "power", "power-le", "arm"]:
                        variant = "Server"
                    if variant == "client":
                        variant = "Client"
                    if variant == "workstation":
                        variant = "Workstation"
                    if variant == "computenode":
                        variant = "ComputeNode"
                    # $arches: ['Server-ppc64le', 'ComputeNode-x86_64', 'Server-aarch64', 'Server-ppc64', 'Client-x86_64', 'Server-s390x', 'Server-x86_64', 'Workstation-x86_64']
                    arches.append("{0}-{1}".format(variant, basearch))
                    platforms[pid] = list(set(arches))
            print "PID, Variants and arches list in manifest:"
            # Variable $platforms format: {"68":["Client-x86_64", "Client-i386"], "69":["Server-x86_64", "Server-i386"]}
            for i in platforms:
                print "{0}: {1}".format(i, platforms[i])

            # Jenkins upstream job parameter 'Product_ID' and 'RHEL_Variant' are both empty
            if self.PIDs == "" and self.VARIANTs == "":
                # Write testing properties files according to platforms listed in manifest
                for pid in platforms:
                    # Generate *.properties files used to trigger downstream jobs
                    for variant_arch in platforms[pid]:
                        self.__generate_properties(variant_arch, pid)

            # Jenkins upstream job parameter 'Product_ID' is not empty
            elif self.PIDs != "":
                for pid in self.PIDs.split(","):
                    if pid not in platforms.keys():
                        print "Warning: PID {0} is not in manifest!".format(pid)
                        continue

                    # Jenkins upstream job parameter 'Product_ID' is not empty, 'RHEL_Variant' is empty
                    if self.VARIANTs == "":
                        # If VARIANTs is empty, then generate *.properties files according to variant_arch under pid in manifest
                        for variant_arch in platforms[pid]:
                            self.__generate_properties(variant_arch, pid)

                    # Jenkins upstream job parameter 'Product_ID' and 'RHEL_Variant' are both not empty
                    else:
                        # Delete those invalid arches which are not in manifest
                        variants = self.__check_arches(self.VARIANTs, platforms[pid])

                        # Generate *.properties files used to trigger downstream jobs
                        for variant_arch in variants:
                            self.__generate_properties(variant_arch, pid)

            # Jenkins upstream job parameter Product_ID is empty, RHEL_Variant is not empty
            else:
                for pid in platforms.keys():
                    # Delete those invalid arches which are not in manifest
                    print "PID {0}:{1}".format(pid, platforms[pid])
                    variants = self.__check_arches(self.VARIANTs, platforms[pid])

                    # Generate *.properties files used to trigger downstream jobs
                    for variant_arch in variants:
                        self.__generate_properties(variant_arch, pid)

            # Generate the final properties file
            output = commands.getoutput("ls | grep properties")
            if output != "":
                for prop_file in output.splitlines():
                    # Content of current properties file
                    # VARIANT=Server
                    # ARCH=i386
                    # PID=90
                    # PID=83
                    # PID=69

                    # Merge several PIDs into one line, such as, merge the above PID lines to PID=90,83,69
                    pid_info = commands.getoutput("cat %s | grep PID | awk -F'=' '{print $2}'" % prop_file).replace('\n', ',')

                    # Delete PID lines from properties file
                    commands.getoutput("sed -i '/PID/d' {0}".format(prop_file))

                    # Content of final *.properties file
                    # VARIANT=Server
                    # ARCH=i386
                    # PID=90,83,69
                    # MANIFEST_URL=http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel6.7/rhel-6.7-beta-blacklist-prod.json
                    # DISTRO=RHEL-7.2-20150904.0
                    # CDN=QA
                    # CANDLEPIN=Stage
                    # BLACKLIST=GA
                    # RELEASE_VERSION=7.2
                    with open("{0}".format(prop_file), 'a+') as f:
                        # Re-write PID line into properties file
                        f.write("PID={0}\n".format(pid_info))

                        # Write other Jenkins job parameters into properties file
                        f.write("Manifest_URL={0}\n".format(self.MANIFEST_URL))
                        f.write("Distro={0}\n".format(self.DISTRO))
                        f.write("CDN={0}\n".format(self.CDN))
                        f.write("Candlepin={0}\n".format(self.CANDLEPIN))
                        f.write("Blacklist={0}\n".format(self.BLACKLIST))
                        f.write("Release_Version={0}\n".format(self.RELEASE_VERSION))
            else:
                print "No eligible testing platform provided!"
        else:
            print "No CDN part provided in manifest!"

    def __generate_properties(self, variant_arch, pid):
        # Content of current *.properties file
        # VARIANT=Server
        # ARCH=i386
        # PID=69
        # PID=83
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

    def __check_arches(self, VARIANTs, VTs_manifest):
        variants = []
        for v in VARIANTs.split(","):
            if v in VTs_manifest:
                variants.append(v)
                print "Requested variant {0} is in manifest!".format(v)
            else:
                print "Warning: requested variant {0} is not in manifest!".format(v)
        return variants


class AnalyzeRHN(object):
    """
    1. Get base testing platforms from manifest, such as ['Client_x86_64', 'Server_s390x', 'Server_x86_64', 'Workstation_x86_64']
    2. Get Jenkins upstream job parameter 'Channels' as CHANNELs and 'RHEL_Variant' as VARIANTs
    3. Get testing platform intersection
       If 'Channels' and 'RHEL_Variant' are both empty
       If 'Channels' is not empty, 'RHEL_Variant' is empty
       If 'Channels' is not empty, 'RHEL_Variant' is not empty
       If 'Channels' is empty, 'RHEL_Variant' is not empty
    4. Generate properties files, such as Server-x86_64.properties, Server-i386.properties, and write VARIANT and ARCH variables
    5. Append other parameters into properties files in order to pass down these params listed in properties files to downstream jobs
    6. Content of properties file:
        VARIANT=Server
        ARCH=i386
        MANIFEST_URL=http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel6.7/rhel-6.7-beta-blacklist-prod.json
        DISTRO=RHEL-7.2-20150904.0
        RHN=QA
    """
    def __init__(self):
        self.DISTRO = os.environ["Distro"]
        self.RHN = os.environ["RHN"]
        self.CHANNELs = "" #os.environ["Channels"]
        self.VARIANTs = os.environ["RHEL_Variant"]
        self.MANIFEST_URL = os.environ["Manifest_URL"]

        # Download and load manifest
        self.MANIFEST_PATH = os.path.join(os.getcwd(), "manifest")
        self.MANIFEST_NAME = os.path.join(self.MANIFEST_PATH, "RHN_MANIFEST.json")
        self.content = download_read_manifest(self.MANIFEST_PATH, self.MANIFEST_NAME, self.MANIFEST_URL)

    def analyze_rhn(self):
        if "rhn" in self.content.keys():
            # Get testing platforms from mainfest
            platforms = []
            rhn = self.content["rhn"]
            for channel in rhn["channels"].keys():
                print channel
                arch = channel.split("-")[1]
                variant = channel.split("-")[2]
                if variant == "server":
                    variant = "Server"
                elif variant == "client":
                    variant = "Client"
                elif variant == "workstation":
                    variant = "Workstation"
                elif variant == "computenode":
                    variant = "ComputeNode"
                platforms.append("{0}-{1}".format(variant, arch))
            platforms = list(set(platforms))
            # ['Server_ppc64le', 'ComputeNode_x86_64', 'Server_aarch64', 'Server_ppc64', 'Client_x86_64', 'Server_s390x', 'Server_x86_64', 'Workstation_x86_64']
            print "Variants and arches list in manifest:", platforms

            testing_platforms = []
            if self.CHANNELs == "" and self.VARIANTs == "":
                testing_platforms = platforms
            elif self.CHANNELs != "":
                pass
            else:
                # Get the intersection of $platforms in manifest and $VARIANTs provided as parameter
                # VARIANTs: ['Server-i386', 'Server-x86_64']
                testing_platforms = list(set(self.VARIANTs.split(",")).intersection(set(platforms)))
            print "Need to do testing on:", testing_platforms

            # Generate properties file to trigger downstream jobs and pass down testing parameters
            # Content of *.properties file
            # VARIANT=Server
            # ARCH=i386
            # MANIFEST_URL=http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel6.7/rhel-6.7-beta-blacklist-prod.json
            # DISTRO=RHEL-7.2-20150904.0
            # RHN=QA
            for file_content in testing_platforms:
                variant = file_content.split("-")[0]
                arch = file_content.split("-")[1]
                with open("{0}.properties".format(file_content), 'w') as f:
                    # Write $variant to new properties file
                    f.write("VARIANT={0}\n".format(variant))

                    # Write $arch to new properties file
                    f.write("ARCH={0}\n".format(arch))

                    # Write other Jenkins job parameters to properties file
                    f.write("Manifest_URL={0}\n".format(self.MANIFEST_URL))
                    f.write("Distro={0}\n".format(self.DISTRO))
                    f.write("RHN={0}\n".format(self.RHN))


class GetPID(object):
    def __init__(self):
        self.PID = []
        self.VARIANT = os.environ["VARIANT"]
        self.ARCH = os.environ["ARCH"]
        self.MANIFEST_URL = os.environ["Manifest_URL"]

        # Download and load manifest
        self.MANIFEST_PATH = os.path.join(os.getcwd(), "manifest")
        self.MANIFEST_NAME = os.path.join(self.MANIFEST_PATH, "CDN_MANIFEST.json")
        self.content = download_read_manifest(self.MANIFEST_PATH, self.MANIFEST_NAME, self.MANIFEST_URL)

    def get_pid(self):
        if "cdn" in self.content.keys():
            # Get PIDs need testing on current $VARIANT and $ARCH
            for pid in self.content["cdn"]["products"]:
                for repo_path in self.content["cdn"]["products"][pid]["Repo Paths"]:
                    basearch = self.content["cdn"]["products"][pid]["Repo Paths"][repo_path]["basearch"]
                    variant = repo_path.split('/')[4]
                    if variant in ["server", "system-z", "power", "power-le", "arm"]:
                        variant = "Server"
                    if variant == "client":
                        variant = "Client"
                    if variant == "workstation":
                        variant = "Workstation"
                    if variant == "computenode":
                        variant = "ComputeNode"
                    if self.VARIANT == variant and self.ARCH == basearch:
                        self.PID.append(pid)
                        break
            # Write $PID into file PID.txt
            with open("PID.txt", 'w') as f:
                f.write(",".join(self.PID))
        else:
            print "No CDN part provided in manifest!"


if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
    else:
        if sys.argv[1] == "cdn":
            cdn = AnalyzeCDN()
            cdn.analyze_cdn()
        elif sys.argv[1] == "rhn":
            rhn = AnalyzeRHN()
            rhn.analyze_rhn()
        elif sys.argv[1] == "pid":
            GetPID().get_pid()
        else:
            pass

