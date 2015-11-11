import re
import logging

from Utils.RemoteSHH import RemoteSHH

class EntitlementBase(object):
    def __init__(self):
        pass

    def get_os_release_version(self, system_info):
        # get release version of current system
        cmd = '''python -c "import yum; yb = yum.YumBase(); print(yb.conf.yumvar)['releasever']"'''
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get current release version...")
        if ret == 0 and "Loaded plugins" in output:
            logging.info("It's successful to get current release version.")
            prog = re.compile('(\d+\S+)\s*')
            result = re.findall(prog, output)
            logging.info("Release version for current system is {0}.".format(result[0]))
            return result[0]
        else:
            logging.error("Test Failed - Failed to get current release version.")
            exit(1)

    def get_os_base_arch(self, system_info):
        # get base arch of current system
        cmd = '''python -c "import yum; yb = yum.YumBase(); print(yb.conf.yumvar)['basearch']"'''
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get current base arch...")
        if(ret == 0 and "Loaded plugins" in output):
            logging.info("It's successful to get current base arch.")
            #prog = re.compile("(\S+\d+.*)\s+")
            #result = re.search(prog, output)
            if "ppc64le" in output:
                base_arch = "ppc64le"
            elif "ppc64" in output:
                base_arch = "ppc64"
            elif "ppc" in output:
                base_arch = "ppc"
            elif "i386" in output:
                base_arch = "i386"
            elif "x86_64" in output:
                base_arch = "x86_64"
            elif "s390x" in output:
                base_arch = "s390x"
            elif "ia64" in output:
                base_arch = "ia64"
            elif "aarch64" in output:
                base_arch = "aarch64"
            else:
                logging.info("No base arch could get from current system.")
                logging.error("Test Failed - Failed to get current base arch.")
                exit(1)
            logging.info("Base arch for current system is %s." % base_arch)
            return base_arch
        else:
            logging.error("Test Failed - Failed to get current base arch.")
            exit(1)

    def cmp_arrays(self, array1, array2):
        # cmp two arrays, get the data in array1 but not in array2
        list_not_in_array2 = []
        for i in array1:
            if i not in array2:
                list_not_in_array2.append(i)
        return list_not_in_array2

    def print_list(self, list):
        for i in list:
            logging.info(i)

    def remove_non_redhat_repo(self, system_info):
        # backup non-redhat repo to avoid bad affection
        cmd = "mkdir -p /tmp/backup_repo/; cp /etc/yum.repos.d/beaker* /tmp/backup_repo/"
        RemoteSHH().run_cmd(system_info, cmd, "Trying to backup non-redhat repos to /tmp/backup_repo/...")

        # remove non-redhat repo
        cmd = "ls /etc/yum.repos.d/ | grep -v redhat.repo | xargs rm -rf"
        RemoteSHH().run_cmd(system_info, cmd, "Trying to delete non-redhat repos to avoid affection...")

    def restore_non_redhat_repo(self, system_info):
        # delete rhn debuginfo repo to remove affection
        cmd = 'cp /tmp/backup_repo/*.repo /etc/yum.repos.d/'
        RemoteSHH().run_cmd(system_info, cmd, "Trying to restore those non-redhat repos...")