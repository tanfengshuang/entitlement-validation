import re
import os
import time
import logging

from Utils.RemoteSHH import RemoteSHH

class EntitlementBase(object):
    def __init__(self):
        pass

    def log_setting(self, variant, arch, server):
        # Write log into specified files
        path = './log/'
        if not os.path.exists(path):
            os.mkdir(path)
        filename = "{0}{1}-{2}-{3}-{4}.log".format(path, variant, arch, server, time.strftime('%Y-%m-%d',time.localtime(time.time())))
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)5s|%(filename)22s:%(lineno)4d|: %(message)s',
                            datefmt='%d %b %Y %H:%M:%S'
                            )
        nor = logging.getLogger()
        formatter = logging.Formatter('%(asctime)s %(levelname)5s|%(filename)22s:%(lineno)4d|: %(message)s')
        filehandler = logging.FileHandler(filename)
        filehandler.suffix = "%Y-%m-%d"
        filehandler.setFormatter(formatter)
        nor.addHandler(filehandler)

    def get_os_release_version(self, system_info):
        # Get release version of current system
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
        # Get base arch of current system
        cmd = '''python -c "import yum; yb = yum.YumBase(); print(yb.conf.yumvar)['basearch']"'''
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get current base arch...")
        if(ret == 0 and "Loaded plugins" in output):
            logging.info("It's successful to get current base arch.")
            base_arch = ""
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
            logging.info("Base arch for current system is {0}.".format(base_arch))
            return base_arch
        else:
            logging.error("Test Failed - Failed to get current base arch.")
            exit(1)

    def cmp_arrays(self, array1, array2):
        # Compare two arrays, get the data in array1 but not in array2
        list_not_in_array2 = []
        for i in array1:
            if i not in array2:
                list_not_in_array2.append(i)
        return list_not_in_array2

    def print_list(self, list):
        for i in list:
            logging.info(i)

    def remove_non_redhat_repo(self, system_info):
        # Backup non-redhat repo
        cmd = "mkdir -p /tmp/backup_repo/; cp /etc/yum.repos.d/beaker* /tmp/backup_repo/"
        RemoteSHH().run_cmd(system_info, cmd, "Trying to backup non-redhat repos to /tmp/backup_repo/...")

        # Remove non-redhat repo
        cmd = "ls /etc/yum.repos.d/* | grep -v redhat.repo | xargs rm -rf"
        RemoteSHH().run_cmd(system_info, cmd, "Trying to delete non-redhat repos to avoid affection...")

        # Check remove result
        cmd = "ls /etc/yum.repos.d/"
        RemoteSHH().run_cmd(system_info, cmd, "Trying to check the result of remove non-redhat repos...")

    def restore_non_redhat_repo(self, system_info):
        # Restore non-redhat repo after testing
        cmd = 'cp /tmp/backup_repo/*.repo /etc/yum.repos.d/'
        RemoteSHH().run_cmd(system_info, cmd, "Trying to restore those non-redhat repos...")

    def get_avail_space(self, system_info):
        ret, output = RemoteSHH().run_cmd(system_info, "df -H | grep home")
        if "home" in output:
            avail_space = output.split()[3]
        else:
            avail_space = "0"
        return avail_space

    def get_master_release(self, system_info):
        ret, release = RemoteSHH().run_cmd(system_info, "lsb_release -r -s", "Trying to restore those non-redhat repos...")
        master_release = release.split(".")[0]
        return master_release

    def extend_system_space(self, system_info):
        # Extend beaker system available space for / partition
        # https://engineering.redhat.com/trac/content-tests/wiki/Content/HowTo/ExtendRootInBeaker
        logging.info("--------------- Begin to extend system space ---------------")
        master_release = self.get_master_release(system_info)

        avail_space = self.get_avail_space(system_info)
        if "G" in avail_space:
            avail_space = avail_space.split("G")[0]
            extend_space = int(avail_space) - 3
            if extend_space <= 0:
                logging.info("No more space to extend")
                logging.info("--------------- End to extend system space ---------------")
                return

            # Check the filesystem(ext4 or xfs), free space and list the lvm volumes
            RemoteSHH().run_cmd(system_info, "cat /etc/fstab", "Trying to get fstab info...")
            RemoteSHH().run_cmd(system_info, "df -h", "Trying to list/check the free space...")
            RemoteSHH().run_cmd(system_info, "lvs", "Trying to list the lvm volumes...")

            # Unmount the home partition and activate LVM
            RemoteSHH().run_cmd(system_info, "umount /home", "Trying to umount home partition...")
            RemoteSHH().run_cmd(system_info, "lvm vgchange -a y", "Trying to activate the volume group...")

            ret, output = RemoteSHH().run_cmd(system_info, "ls /dev/mapper/ | grep home", "Trying to get home partition name...")
            lvm_home = output.splitlines()[0]
            ret, output = RemoteSHH().run_cmd(system_info, "ls /dev/mapper/ | grep root", "Trying to get root partition name...")
            lvm_root = output.splitlines()[0]
            """
            print "**************", lvm_home
            print "**************", lvm_root
            print "resize2fs -f /dev/mapper/{0} 1G".format(lvm_home)
            print "lvreduce -L1G /dev/mapper/{0}".format(lvm_home)
            print "lvextend -L+{0}G  /dev/mapper/{1}".format(extend_space, lvm_root)
            print "resize2fs /dev/mapper/{0}".format(lvm_root), "Trying to resize2fs root partition..."
            print "mount /home"
            """
            if master_release in ["5", "6"]:
                # Shrink the home partition
                ret, output = RemoteSHH().run_cmd(system_info, "resize2fs -f /dev/mapper/{0} 1G".format(lvm_home), "Trying to resize2fs home partition...", timeout=None)
                if "Resizing the filesystem on" in output:
                    logging.info("Succeed to resize2fs home partition to 1G.")
                else:
                    logging.warning("Failed to resize2fs home partition to 1G.")

                ret, output = RemoteSHH().run_cmd_interact(system_info, "lvreduce -L1G /dev/mapper/{0}".format(lvm_home), "Trying to lvreduce home partition...")
                if "successfully resized" in output:
                    logging.info("Succeed to lvreduce home partition to 1G.")
                else:
                    logging.warning("Failed to lvreduce home partition to 1G.")

                # Extend the root partition
                ret, output = RemoteSHH().run_cmd(system_info, "lvextend -L+{0}G /dev/mapper/{1}".format(extend_space, lvm_root), "Trying to lvextend root partition...", timeout=None)
                if "successfully resized" in output:
                    logging.error("Succeed to lvextend {0}G for root partition.".format(avail_space))
                elif "Insufficient free space" in output:
                    logging.warning("Insufficient free space when lvextend root partition.")
                else:
                    logging.warning("Failed to lvextend {0}G for root partition.".format(avail_space))

                ret, output = RemoteSHH().run_cmd(system_info, "resize2fs /dev/mapper/{0}".format(lvm_root), "Trying to resize2fs root partition...", timeout=None)
                if "Performing an on-line resize" in output:
                    logging.info("Succeed to resize2fs root partition.")
                else:
                    logging.warning("Failed to resize2fs root partition.")

                # Remount the home partition
                RemoteSHH().run_cmd(system_info, "mount /home", "Trying to umount home partition...")

                # Check root partition after extend space
                RemoteSHH().run_cmd(system_info, "df -H", "Trying to check root partition after extend space...")

            elif master_release == "7":
                # Delete home partition
                ret, output = RemoteSHH().run_cmd_interact(system_info, "lvremove /dev/mapper/{0}".format(lvm_home), "Trying to delete home partition")
                if "successfully removed" in output:
                    logging.info("Succeed to remove home partition.")
                else:
                    logging.warning("Succeed to remove home partition.")

                # Extend root partition
                ret, output = RemoteSHH().run_cmd(system_info, "lvextend -L+{0}G /dev/mapper/{1}".format(extend_space, lvm_root), "Trying to lvextend root partition...", timeout=None)
                if "successfully resized" in output:
                    logging.info("Succeed to lvextend {0}G for root partition.".format(avail_space))
                elif "Insufficient free space" in output:
                    logging.warning("Insufficient free space when lvextend root partition.")
                else:
                    logging.warning("Succeed to lvextend {0}G for root partition.".format(avail_space))

                RemoteSHH().run_cmd(system_info, "xfs_growfs /", "Trying to xfs_growfs root partition", timeout=None)

                # Check root partition after extend space
                RemoteSHH().run_cmd(system_info, "df -H", "Trying to check root partition after extend space...")
            else:
                logging.error("Failed to extend space!")
        else:
            logging.info("No space to extend")

        logging.info("--------------- End to extend system space ---------------")



