import re
import os
import time
import logging

from Utils.RemoteSHH import RemoteSHH

# Create logger
logger = logging.getLogger("entLogger")


class EntitlementBase(object):
    def log_setting(self, variant, arch, server, pid=None):
        # Write log into specific files
        log_path = './log/'
        case_log_path = os.path.join(log_path, pid)
        if not os.path.exists(log_path):
            os.mkdir(log_path)

        if not os.path.exists(case_log_path):
            os.mkdir(case_log_path)

        if pid == None:
            filename_debug = "{0}/DEBUG-{1}-{2}-{3}-{4}.log".format(case_log_path, variant, arch, server, time.strftime('%Y-%m-%d',time.localtime(time.time())))
            filename_info = "{0}/INFO-{1}-{2}-{3}-{4}.log".format(case_log_path, variant, arch, server, time.strftime('%Y-%m-%d',time.localtime(time.time())))
            filename_error = "{0}/ERROR-{1}-{2}-{3}-{4}.log".format(case_log_path, variant, arch, server, time.strftime('%Y-%m-%d',time.localtime(time.time())))
        else:
            filename_debug = "{0}/DEBUG-{1}-{2}-{3}-{4}-{5}.log".format(case_log_path, variant, arch, server, pid, time.strftime('%Y-%m-%d',time.localtime(time.time())))
            filename_info = "{0}/INFO-{1}-{2}-{3}-{4}-{5}.log".format(case_log_path, variant, arch, server, pid, time.strftime('%Y-%m-%d',time.localtime(time.time())))
            filename_error = "{0}/ERROR-{1}-{2}-{3}-{4}-{5}.log".format(case_log_path, variant, arch, server, pid, time.strftime('%Y-%m-%d',time.localtime(time.time())))

        formatter = logging.Formatter('%(asctime)s %(levelname)5s|%(filename)22s:%(lineno)4d|: %(message)s')

        # Set debug log file
        file_handler_debug = logging.FileHandler(filename_debug)
        file_handler_debug.suffix = "%Y-%m-%d"
        file_handler_debug.setFormatter(formatter)
        file_handler_debug.setLevel(logging.DEBUG)

        # Set info log file
        file_handler_info = logging.FileHandler(filename_info)
        file_handler_info.suffix = "%Y-%m-%d"
        file_handler_info.setFormatter(formatter)
        file_handler_info.setLevel(logging.INFO)

        # Set error log file
        file_handler_error = logging.FileHandler(filename_error)
        file_handler_error.suffix = "%Y-%m-%d"
        file_handler_error.setFormatter(formatter)
        file_handler_error.setLevel(logging.ERROR)

        # Print log on the console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        return file_handler_debug, file_handler_info, file_handler_error, console_handler

    def ntpdate_redhat_clock(self, system_info):
        # Synchronize system time with clock.redhat.com, it's a workaround when system time is not correct,
        # commands "yum repolist" and "subscription-manager repos --list" return nothing
        cmd = 'ntpdate clock.redhat.com'
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to ntpdate system time with clock of redhat.com...")
        if ret == 0 or "the NTP socket is in use, exiting" in output:
            logger.info("It's successful to ntpdate system time with clock of redhat.com.")
        else:
            logger.warning("Test Failed - Failed to ntpdate system time with clock of redhat.com.")

    def get_os_release_version(self, system_info):
        # Get release version of current system
        cmd = '''python -c "import yum; yb = yum.YumBase(); print(yb.conf.yumvar)['releasever']"'''
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get current release version...")
        if ret == 0 and "Loaded plugins" in output:
            logger.info("It's successful to get current release version.")
            prog = re.compile('(\d+\S+)\s*')
            result = re.findall(prog, output)
            logger.info("Release version for current system is {0}.".format(result[0]))
            return result[0]
        else:
            assert False, "Test Failed - Failed to get current release version."

    def get_os_base_arch(self, system_info):
        # Get base arch of current system
        cmd = '''python -c "import yum; yb = yum.YumBase(); print(yb.conf.yumvar)['basearch']"'''
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get current base arch...")
        if ret == 0 and "Loaded plugins" in output:
            logger.info("It's successful to get current base arch.")
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
                logger.error("No base arch could get from current system.")
                assert False, "Test Failed - Failed to get current base arch."
            logger.info("Base arch for current system is {0}.".format(base_arch))
            return base_arch
        else:
            assert False, "Test Failed - Failed to get current base arch."

    def write_polarion_props(self, system_info):
        # Generate file polarion.prop on jenkins slave machine for Polarion case properties to create run automatically
        master_relase = self.get_master_release(system_info)
        cmd = "cat ../polarion.prop | grep Master_Release"
        ret, output = RemoteSHH().run_cmd(None, cmd, "Trying to get current base arch...")
        if "Master_Release" not in output:
            with open("../polarion.prop", 'a+') as f:
                f.write("Master_Release={0}".format(master_relase))

    def cmp_arrays(self, array1, array2):
        # Compare two arrays, get the data in array1 but not in array2
        list_not_in_array2 = []
        for i in array1:
            if i not in array2:
                list_not_in_array2.append(i)
        return list_not_in_array2

    def print_list(self, list):
        if len(list) > 100:
            logging.info("<< Note: since the output is too long(more than 100 lines) here, logged it as debug info. >>")
            for i in list:
                logger.debug(i)
        else:
            for i in list:
                logger.info(i)

    def remove_non_redhat_repo(self, system_info):
        # Backup non-redhat repo
        backup_path = "/tmp/backup_repo"
        cmd = "mkdir -p {0}; cp /etc/yum.repos.d/beaker* {0}".format(backup_path)
        RemoteSHH().run_cmd(system_info, cmd, "Trying to backup non-redhat repos to {0}...".format(backup_path))

        # Remove non-redhat repo
        cmd = "ls /etc/yum.repos.d/* | grep -v redhat.repo | xargs rm -rf"
        RemoteSHH().run_cmd(system_info, cmd, "Trying to delete non-redhat repos to avoid affection...")

        # Check remove result
        cmd = "ls /etc/yum.repos.d/"
        RemoteSHH().run_cmd(system_info, cmd, "Trying to check the result of remove non-redhat repos...")

    def restore_non_redhat_repo(self, system_info):
        # Restore non-redhat repo after testing
        path = "/tmp/backup_repo/*.repo"
        cmd = 'cp {0} /etc/yum.repos.d/'.format(path)
        RemoteSHH().run_cmd(system_info, cmd, "Trying to restore those non-redhat repos...")

    def get_sys_pkglist(self, system_info):
        # Get system packages list before installation testing, and then make sure these packages will not be removed during installation testing.
        cmd = 'rpm -qa --qf "%{name}\n"'
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list all packages in system before installation testing...")
        if ret == 0:
            sys_pkglist = output.splitlines()
            logger.info("It's successful to get {0} packages from the system.\n".format(len(sys_pkglist)))
            return sys_pkglist
        else:
            assert False, "Test Failed - Failed to list all packages in system before level3."

    def remove_pkg(self, system_info, pkg, repo_channel):
        # Remove a package after install in order to resolve dependency issue which described in
        # https://bugzilla.redhat.com/show_bug.cgi?id=1272902
        cmd = "yum remove -y {0}".format(pkg)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to remove package {0} of repo/channel {1}...".format(pkg, repo_channel))
        if ret == 0:
            logger.info("It's successful to remove package '{0}' of repo/channel {1}.\n".format(pkg, repo_channel))
            return True
        else:
            logger.warning("Warning -- Can't remove package '{0}' of repo/channel {1}.\n".format(pkg, repo_channel))
            return False

    def get_avail_space(self, system_info):
        ret, output = RemoteSHH().run_cmd(system_info, "df -H | grep home")
        if "home" in output:
            avail_space = output.split()[3]
        else:
            avail_space = "0"
        return avail_space

    def get_master_release(self, system_info):
        ret, output = RemoteSHH().run_cmd(system_info, "rpm -q redhat-lsb", "Trying to check if command redhat-lsb is installed...")
        if "not installed" in output:
            RemoteSHH().run_cmd(system_info, "yum install -y redhat-lsb", "Trying to check if command redhat-lsb is installed...")
        ret, release = RemoteSHH().run_cmd(system_info, "lsb_release -r -s", "Trying to restore those non-redhat repos...")
        master_release = release.split(".")[0]
        return master_release

    def extend_system_space(self, system_info):
        # Extend beaker system available space for / partition
        # https://engineering.redhat.com/trac/content-tests/wiki/Content/HowTo/ExtendRootInBeaker
        logger.info("--------------- Begin to extend system space ---------------")
        master_release = self.get_master_release(system_info)

        avail_space = self.get_avail_space(system_info)
        if "G" in avail_space:
            avail_space = avail_space.split("G")[0]
            extend_space = int(float(avail_space)) - 3
            if extend_space <= 0:
                logger.info("No more space to extend")
                logger.info("--------------- End to extend system space ---------------")
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

            if master_release in ["5", "6"]:
                # Shrink the home partition
                ret, output = RemoteSHH().run_cmd(system_info, "resize2fs -f /dev/mapper/{0} 1G".format(lvm_home), "Trying to resize2fs home partition...", timeout=None)
                if "Resizing the filesystem on" in output:
                    logger.info("Succeed to resize2fs home partition to 1G.")
                else:
                    logger.warning("Failed to resize2fs home partition to 1G.")

                ret, output = RemoteSHH().run_cmd_interact(system_info, "lvreduce -L1G /dev/mapper/{0}".format(lvm_home), "Trying to lvreduce home partition...")
                if "successfully resized" in output:
                    logger.info("Succeed to lvreduce home partition to 1G.")
                else:
                    logger.warning("Failed to lvreduce home partition to 1G.")

                # Extend the root partition
                ret, output = RemoteSHH().run_cmd(system_info, "lvextend -L+{0}G /dev/mapper/{1}".format(extend_space, lvm_root), "Trying to lvextend root partition...", timeout=None)
                if "successfully resized" in output:
                    logger.info("Succeed to lvextend {0}G for root partition.".format(avail_space))
                elif "Insufficient free space" in output:
                    logger.warning("Insufficient free space when lvextend root partition.")
                else:
                    logger.warning("Failed to lvextend {0}G for root partition.".format(avail_space))

                ret, output = RemoteSHH().run_cmd(system_info, "resize2fs /dev/mapper/{0}".format(lvm_root), "Trying to resize2fs root partition...", timeout=None)
                if "Performing an on-line resize" in output:
                    logger.info("Succeed to resize2fs root partition.")
                else:
                    logger.warning("Failed to resize2fs root partition.")

                # Remount the home partition
                RemoteSHH().run_cmd(system_info, "mount /home", "Trying to umount home partition...")

                # Check root partition after extend space
                RemoteSHH().run_cmd(system_info, "df -H", "Trying to check root partition after extend space...")

            elif master_release == "7":
                # Delete home partition
                ret, output = RemoteSHH().run_cmd_interact(system_info, "lvremove /dev/mapper/{0}".format(lvm_home), "Trying to delete home partition")
                if "successfully removed" in output:
                    logger.info("Succeed to remove home partition.")
                else:
                    logger.warning("Succeed to remove home partition.")

                # Extend root partition
                ret, output = RemoteSHH().run_cmd(system_info, "lvextend -L+{0}G /dev/mapper/{1}".format(extend_space, lvm_root), "Trying to lvextend root partition...", timeout=None)
                if "successfully resized" in output:
                    logger.info("Succeed to lvextend {0}G for root partition.".format(avail_space))
                elif "Insufficient free space" in output:
                    logger.warning("Insufficient free space when lvextend root partition.")
                else:
                    logger.warning("Succeed to lvextend {0}G for root partition.".format(avail_space))

                RemoteSHH().run_cmd(system_info, "xfs_growfs /", "Trying to xfs_growfs root partition", timeout=None)

                # Check root partition after extend space
                RemoteSHH().run_cmd(system_info, "df -H", "Trying to check root partition after extend space...")
            else:
                logger.warning("Failed to extend space!")
        else:
            logger.info("No space to extend")

        logger.info("--------------- End to extend system space ---------------")



