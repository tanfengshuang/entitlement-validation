import os
import sys
import json
import commands

# test data
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel6.7/rhel-6.7-beta-blacklist-prod.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel5.10/rhel5.10-rc-1.3.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel7.2/rhel-7.2-snapshot1-qa-cdn.json
# http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhcmsys8/15017-package-manifest.json


def usage():
    print "Usage: {0} cdn|CDN|rhn|RHN|sat|SAT".format(sys.argv[0])
    exit(1)

def download_read_manifest(MANIFEST_PATH, MANIFEST_URL):
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

    # open and read MANIFEST.json
    content = json.load(open(MANIFEST_PATH, 'r'))
    return content


class AnalyzeCDN(object):
    def __init__(self):
        self.pid_file = "pid.txt"
        self.variant_file = "variant.txt"
        self.baseinfo_file = "baseinfo.txt"
        self.MANIFEST_PATH = "MANIFEST.json"
        self.MANIFEST_URL = commands.getoutput("cat %s | grep MANIFEST_URL | awk -F'=' '{print $2}'" % (self.baseinfo_file))
        self.content = download_read_manifest(self.MANIFEST_PATH, self.MANIFEST_URL)

    def analyze_cdn(self):
        # read PID and VARIANT from jenkins parameters
        PIDs, VARIANTs = self.__get_pid_variant()

        # parse MANIFEST.json to get test platforms
        if "cdn" in self.content.keys():
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
                # PID=69
                for pid in platforms:
                    # generate *.properties files used to trigger downstream jobs
                    for variant_arch in platforms[pid]:
                        self.__generate_properties(variant_arch, pid)
            elif PIDs != "":
                for pid in PIDs.split(","):
                    if pid not in platforms.keys():
                        print "Warning: PID {0} is not in manifest!".format(pid)
                        continue
                    if VARIANTs == "":
                        # generate *.properties files used to trigger downstream jobs
                        for variant_arch in platforms[pid]:
                            self.__generate_properties(variant_arch, pid)
                    else:
                        # Delete those invalid arches which are not in manifest
                        variants = self.__check_arches(VARIANTs, platforms[pid])
                        # generate *.properties files used to trigger downstream jobs
                        for variant_arch in variants:
                            self.__generate_properties(variant_arch, pid)
            else:
                # Delete those invalid arches which are not in manifest
                variants = self.__check_arches(VARIANTs, platforms[pid])
                # generate *.properties files used to trigger downstream jobs
                for variant_arch in variants:
                    self.__generate_properties(variant_arch, pid)

            # copy the content of file $baseinfo_file to *.properties
            output = commands.getoutput("ls | grep properties")
            if output != "":
                for file in output.splitlines():
                    if output != "":
                        # merge several PIDs into one line, such as, merge the following lines to PID=90,83,69
                        # PID=90
                        # PID=83
                        # PID=69
                        PID_info = commands.getoutput("cat %s | grep PID | awk -F'=' '{print $2}'" % file).replace('\n', ',')
                        with open("{0}".format(file), 'w') as f1:
                            # write non-PID lines
                            f1.write(commands.getoutput("cat {0} | grep -v PID".format(file)))
                            # write PID lines to one line - PID=90,83,69
                            f1.write("PID={0}\n".format(PID_info))
                    with open("{0}".format(file), 'a+') as f1:
                        # write $baseinfo_file content to *.properties
                        with open("{0}".format(self.baseinfo_file), 'r') as f2:
                            f1.write(f2.read())
        else:
            print "No CDN part provided in manifest!"

    def __generate_properties(self, variant_arch, pid):
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

    def __get_pid_variant(self):
        PIDs = ""
        VARIANTs = ""
        if os.path.exists(self.pid_file):
            with open("{0}".format(self.pid_file), 'r') as f:
                PIDs = f.read().splitlines()[0]
        if os.path.exists(self.variant_file):
            with open("{0}".format(self.variant_file), 'r') as f:
                VARIANTs = f.read().splitlines()[0]
        return PIDs, VARIANTs

    def __check_arches(self, VARIANTs, VTs):
        variants = []
        for v in VARIANTs.split(","):
            if v in VTs:
                variants.append(v)
            else:
                print "Warning: variant {0} is not in manifest!".format(v)
        return variants


class AnalyzeRHN(object):
    def __init__(self):
        self.channel_file = "channel.txt"
        self.variant_file = "variant.txt"
        self.baseinfo_file = "baseinfo.txt"
        self.MANIFEST_PATH = "MANIFEST.json"
        self.MANIFEST_URL = commands.getoutput("cat %s | grep MANIFEST_URL | awk -F'=' '{print $2}'" % (self.baseinfo_file))
        self.content = download_read_manifest(self.MANIFEST_PATH, self.MANIFEST_URL)

    def analyze_rhn(self):
        # read PID and VARIANT from jenkins parameters
        CHANNELs, VARIANTs = self.__get_channel_variant()

        # parse MANIFEST.json to get test platforms
        if "rhn" in self.content.keys():
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
            if CHANNELs == "" and VARIANTs == "":
                # ready to write testing properties files
                # *.properties file content
                # MANIFEST_URL=http://hp-z220-11.qe.lab.eng.nay.redhat.com/projects/content-sku/manifests/rhel6.7/rhel-6.7-beta-blacklist-prod.json
                # DISTRO=RHEL-7.2-20150904.0
                # CDN=QA
                # VARIANT=Server
                # ARCH=i386
                testing_platforms = platforms
            elif CHANNELs != "":
                pass
            else:
                # get the intersection of $platforms in manifest and $VARIANTs provided as parameter
                testing_platforms = list(set(VARIANTs.split(",")).intersection(set(platforms)))
            print "Need to do testing on:", testing_platforms

            # generate properties used for triggering downstream jobs
            for file_content in testing_platforms:
                variant = file_content.split("-")[0]
                arch = file_content.split("-")[1]
                with open("{0}.properties".format(file_content), 'w') as f1:
                    # write $variant to new properties file
                    f1.write("VARIANT={0}\n".format(variant))
                    # write $arch to new properties file
                    f1.write("ARCH={0}\n".format(arch))
                    # copy content of file $baseinfo_file to new properties file
                    with open("{0}".format(self.baseinfo_file), 'r') as f2:
                        f1.write(f2.read())
        else:
            print "No RHN part provided in manifest!"

    def __get_channel_variant(self):
        CHANNELs = ""
        VARIANTs = ""
        if os.path.exists(self.channel_file):
            with open("{0}".format(self.channel_file), 'r') as f:
                CHANNELs = f.read().splitlines()[0]
        if os.path.exists(self.variant_file):
            with open("{0}".format(self.variant_file), 'r') as f:
                VARIANTs = f.read().splitlines()[0]
        return CHANNELs, VARIANTs

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
        else:
            pass

