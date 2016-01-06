import logging

from Utils.RemoteSHH import RemoteSHH
from Utils.EntitlementBase import EntitlementBase
from SAT5.SAT5ReadXML import SAT5ReadXML

# Create logger
logger = logging.getLogger("entLogger")


class SAT5Verification(EntitlementBase):
    def download_cert(self, system_info, sat5_server):
        cert_download_path = "/usr/share/rhn/RHN-ORG-TRUSTED-SSL-CERT"
        RemoteSHH().run_cmd(system_info, "rm -rf {0}".format(cert_download_path), "Trying to remove old cert {0} before download it...".format(cert_download_path))
        cmd = "wget http://%s/pub/RHN-ORG-TRUSTED-SSL-CERT -O %s" % (sat5_server, cert_download_path)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to download cert {0}...".format(cert_download_path))
        if ret == 0:
            logger.info("It's successful to download ssl CA cert {0}.".format(cert_download_path))
            return True
        else:
            logger.error("Test Failed - Failed to download ssl CA cert {0}.".format(cert_download_path))
            return False

    def update_up2date(self, system_info, server_url):
        # sslCACert default value:
        # RHEL6: sslCACert=/usr/share/rhn/RHNS-CA-CERT
        # RHEL7: sslCACert=/usr/share/rhn/RHN-ORG-TRUSTED-SSL-CERT
        up2date_path = "/etc/sysconfig/rhn/up2date"
        cert = "/usr/share/rhn/RHN-ORG-TRUSTED-SSL-CERT"
        cmd = "sed -e '/sslCACert=/d' -e '/^sslCACert/a\sslCACert={0}/usr/share/rhn/shuang' {1}".format(cert, up2date_path)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to set sslCACert in {0}...".format(up2date_path))
        if ret == 0:
            logger.info("It's successful to set sslCACert to {0} in {1}.".format(cert, up2date_path))
        else:
            logger.error("Test Failed - Failed to set sslCACert to {0} in {1}.".format(cert, up2date_path))
            return False

        cmd = "sed -e '/serverURL=/d' -e '/^serverURL/a\serverURL={0}' {1}".format(server_url, up2date_path)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to set serverUrl in {0}...".format(up2date_path))
        if ret == 0:
            logger.info("It's successful to set serverURL to {0} in {1}.".format(server_url, up2date_path))
        else:
            logger.error("Test Failed - Failed to set serverURL to {0} in {1}.".format(server_url, up2date_path))
            return False

        return True

    def register(self, system_info, username, password, server_url):
        cmd = "rhnreg_ks --username=%s --password=%s --serverUrl=%s" % (username, password, server_url)

        if self.isregistered(system_info):
            if not self.unregister(system_info):
                logger.info("The system is failed to unregister from Satellite 5 server, try to use '--force'!")
                cmd += " --force"

        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to register to Satellite 5 server...")
        if ret == 0:
            logger.info("It's successful to register to Satellite 5 server.")
            cmd = "rm -rf /var/cache/yum/*"
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to clean the yum cache after register...")
            if ret == 0:
                logger.info("It's successful to clean the yum cache.")
            else:
                logger.warning("Failed to clean the yum cache.")
            return True
        else:
            # Error Message:
            # Invalid username/password combination
            logger.error("Test Failed - Failed to register with Satellite 5 server.")
            return False

    def isregistered(self, system_info,):
        cmd = "ls /etc/sysconfig/rhn/systemid"
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check if registered to Satellite 5 server...")
        if ret == 0:
            logger.info("The system is registered to Satellite 5 server now.")
            return True
        else:
            logger.info("The system is not registered to Satellite 5 server now.")
            return False

    def unregister(self, system_info,):
        cmd = "rm -rf /etc/sysconfig/rhn/systemid"
        (ret1, output1) = RemoteSHH().run_cmd(system_info, cmd, "Trying to unregister from Satellite 5 - delete systemid...")

        cmd = "sed -i 's/enabled = 1/enabled = 0/' /etc/yum/pluginconf.d/rhnplugin.conf"
        (ret2, output2) = RemoteSHH().run_cmd(system_info, cmd, "Trying to unregister from Satellite 5 - modify rhnplugin.conf...")

        if ret1 == 0 and ret2 == 0:
            logger.info("It's successful to unregister from Satellite 5 server.")
            return True
        else:
            logger.error("Test Failed - Failed to unregister from Satellite 5 server.")
            return False

    def add_channels(self, system_info, username, password, channels):
        channel_default = []
        cmd = "rhn-channel --list --user=%s --password=%s" % (username, password)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list the channel which was added by default after register...")
        if ret == 0:
            channel_default = output.splitlines()
            logger.info("It's successful to get default channel from Satellite 5 server: %s" % channel_default)

        if not isinstance(channels, list):
            channels = [channels]

        for channel in channels:
            if channel not in channel_default:
                # Add channel
                cmd = "rhn-channel --add --channel=%s --user=%s --password=%s" % (channel, username, password)
                ret, output = RemoteSHH().run_cmd(system_info, cmd, "add channel %s" % channel)

            cmd = "rhn-channel --list --user=%s --password=%s" % (username, password)
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check if channel {0} was added successfully...".format(channel))
            channel_added = output.splitlines()

            if ret == 0 and channel in channel_added:
                logger.info("It's successful to add channel %s." % channel)
                return True
            else:
                logger.error("Test Failed - Failed to add channel %s." % channel)
                return False

    def remove_channels(self, system_info, username, password, channels=None):
        if channels == None:
            cmd = "rhn-channel --list --user=%s --password=%s" % (username, password)
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list all added channel already...")
            channels = output.splitlines()

        if not isinstance(channels, list):
            channels = [channels]

        for channel in channels:
            cmd = "rhn-channel --remove --channel=%s --user=%s --password=%s" % (channel, username, password)
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to remove channel {0}".format(channel))
            if ret == 0:
                logger.info("It's successful to remove channel %s." % channel)
                return True
            else:
                logger.info("Test Failed - Failed to remove channel %s." % channel)
                return False

    def get_channels_from_manifest(self, manifest_xml, current_arch, variant):
        # Get all channels from manifest which need testing
        repo_filter = "%s-%s" % (current_arch, variant.lower())
        logger.info("Testing repo filter: {0}".format(repo_filter))

        all_channel_list = SAT5ReadXML().get_channel_list(manifest_xml)
        channel_list = [channel for channel in all_channel_list if repo_filter in channel]

        if len(channel_list) == 0:
            logger.error("Got 0 channel from packages manifest")
            logger.error("Test Failed - Got 0 channel from packages manifest.")
            return []
        else:
            logger.info('Got {0} channels from packages manifest:'.format(len(all_channel_list)))
            self.print_list(all_channel_list)
            return channel_list

    def verify_channels(self, system_info, manifest_xml, username, password, current_arch, variant):
        # For now, this function can be only tested on RHEL6, as there is no param --available-channels on RHEL5
        logger.info("--------------- Begin to verify channel ---------------")
        # Get all channels which are not added
        available_channels = []
        cmd = "rhn-channel --available-channels --user=%s --password=%s" % (username, password)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get available channels with command rhn-channel...")
        if ret == 0:
            available_channels = output.splitlines()
        else:
            logger.error("Failed to get available channels.")

        # Get all channels which are already added
        added_channels = []
        cmd = "rhn-channel --list --user=%s --password=%s" % (username, password)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get added channels with command rhn-channel...")
        if ret == 0:
            added_channels = output.splitlines()
        else:
            logger.error("Failed to get added channels.")

        channels = available_channels + added_channels

        # Get all channels from manifest which are needed testing
        channels_manifest = self.get_channels_from_manifest(manifest_xml, current_arch, variant)
        list1 = self.cmp_arrays(channels_manifest, channels)
        if len(list1) > 0:
            logger.error("Failed to verify channel.")
            logger.info('Below are channels in provided manifest but not in rhn-channel:')
            self.print_list(list1)
            logger.error("--------------- End to verify channel: FAIL ---------------")
            logger.error("Test Failed - Failed to verify channel.")
            return False
        else:
            logger.info("All expected channels exist in test list!")
            logger.info("--------------- End to verify channel: PASS ---------------")
            return True

    def installation(self, system_info, manifest_xml, channel):
        # Install binary packages with yum
        # There are source rpms in channels, but they can only be downloaded through the customer portal web site.  They aren't exposed to yum/yumdownloader/repoquery.
        # RHN APIs that can be used to query the source packages available, but the APIs are only available to RHN admins. So, let's not worry about SRPMs for now.
        # Download source rpms from the customer portal web site - ignored for now
        logger.info("--------------- Begin to verify packages full installation for channel {0} ---------------".format(channel))

        # Get all packages already installed in testing system before installation testing
        system_pkglist = self.get_sys_pkglist(system_info)

        # Store the failed packages when 'yum remove'.
        remove_failed_pkglist = []

        # Get packages from manifest
        package_list = SAT5ReadXML().get_package_list(manifest_xml, channel)
        logger.info("There are {0} packages need to install for channel {0}.".format(len(package_list), package_list))
        self.print_list(package_list)

        result = True
        number = 0
        total_number = len(package_list)
        for pkg in package_list:
            number += 1
            cmd = "yum install -y %s" % pkg
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to yum install package {0} of channel {1}".format(pkg, channel))

            if ret == 0:
                if ("Complete!" in output) or ("Nothing to do" in output) or ("conflicts" in output):
                    logger.info("It's successful to install package [{0}/{1}] {2} of channel {3}...".format(number, total_number, pkg, channel))
                else:
                    logger.error("Test Failed - Failed to install package [{0}/{1}] {2} of channel {3}...".format(number, total_number, pkg, channel))
                    result = False
            else:
                if "conflicts" in output:
                    logger.info("It's successful to install package [{0}/{1}] {2} of channel {3}...".format(number, total_number, pkg, channel))
                else:
                    logger.error("Test Failed - Failed to install package [{0}/{1}] {2} of channel {3}...".format(number, total_number, pkg, channel))
                    result = False

            if result:
                if pkg not in system_pkglist:
                    # Remove package if it is not in the system package list.
                    # It is used to solve the dependency issue which describe in https://bugzilla.redhat.com/show_bug.cgi?id=1272902.
                    if not self.remove_pkg(system_info, pkg, channel):
                        remove_failed_pkglist.append(pkg)
                        logging.warning("Failed to remove {0} of channel {1}.".format(pkg, channel))

        if len(remove_failed_pkglist) != 0:
            logger.warning("Failed to remove following {0} packages for channel {1}:".format(len(remove_failed_pkglist), channel))
            self.print_list(remove_failed_pkglist)

        if result:
            logger.info("--------------- End to verify packages full installation for channel {0}: PASS ---------------".format(channel))
        else:
            logger.error("--------------- End to verify packages full installation for channel {0}: FAIL ---------------".format(channel))
        return result
