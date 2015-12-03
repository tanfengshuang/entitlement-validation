import logging

from Utils.RemoteSHH import RemoteSHH
from Utils.EntitlementBase import EntitlementBase
from RHN.RHNReadXML import RHNReadXML

class RHNVerification(EntitlementBase):
    def __init__(self):
        pass

    def register(self, system_info, username, password, server_url):
        cmd = "rhnreg_ks --username=%s --password=%s --serverUrl=%s" % (username, password, server_url)

        if self.isregistered(system_info):
            if not self.unregister(system_info):
                logging.info("The system is failed to unregister from rhn server, try to use '--force'!")
                cmd += " --force"

        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to register to rhn server...")
        if ret == 0:
            logging.info("It's successful to register to rhn server.")
            cmd = "rm -rf /var/cache/yum/*"
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to clean the yum cache after register...")
            if ret == 0:
                logging.info("It's successful to clean the yum cache.")
            else:
                logging.info("Failed to clean the yum cache.")
            return True
        else:
            #Error Message:
            #Invalid username/password combination
            logging.error("Test Failed - Failed to register to rhn server.")
            exit(1)

    def isregistered(self, system_info,):
        cmd = "ls /etc/sysconfig/rhn/systemid"
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check if registered to rhn...")
        if ret == 0:
            logging.info("The system is registered to rhn server now.")
            return True
        else:
            logging.info("The system is not registered to rhn server now.")
            return False

    def unregister(self, system_info,):
        cmd = "rm -rf /etc/sysconfig/rhn/systemid"
        (ret1, output1) = RemoteSHH().run_cmd(system_info, cmd, "Trying to unregister from rhn - delete systemid...")

        cmd = "sed -i 's/enabled = 1/enabled = 0/' /etc/yum/pluginconf.d/rhnplugin.conf"
        (ret2, output2) = RemoteSHH().run_cmd(system_info, cmd, "Trying to unregister from rhn - modify rhnplugin.conf...")

        if ret1 == 0 and ret2 == 0:
            logging.info("It's successful to unregister from rhn server.")
            return True
        else:
            logging.error("Test Failed - Failed to unregister from rhn server.")
            return False

    def add_channels(self, system_info, username, password, channels):
        channel_default = []
        cmd = "rhn-channel --list --user=%s --password=%s" % (username, password)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to list the channel which was added by default after register...")
        if ret == 0:
            channel_default = output.splitlines()
            logging.info("It's successful to get default channel from rhn server: %s" % channel_default)

        if not isinstance(channels, list):
            channels = [channels]

        for channel in channels:
            if channel not in channel_default:
                # add channel
                cmd = "rhn-channel --add --channel=%s --user=%s --password=%s" % (channel, username, password)
                ret, output = RemoteSHH().run_cmd(system_info, cmd, "add channel %s" % channel)

            cmd = "rhn-channel --list --user=%s --password=%s" % (username, password)
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to check if channel {0} was added successfully...".format(channel))
            channel_added = output.splitlines()

            if ret == 0 and channel in channel_added:
                logging.info("It's successful to add channel %s." % channel)
                return True
            else:
                logging.error("Test Failed - Failed to add channel %s." % channel)
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
                logging.info("It's successful to remove channel %s." % channel)
                return True
            else:
                logging.info("Test Failed - Failed to remove channel %s." % channel)
                return False

    def get_channels_from_manifest(self, manifest_xml, current_arch, variant):
        # get all channels from manifest which need testing
        repo_filter = "%s-%s" % (current_arch, variant.lower())
        logging.info("testing repo filter: {0}".format(repo_filter))

        all_channel_list = RHNReadXML().get_channel_list(manifest_xml)
        channel_list = [channel for channel in all_channel_list if repo_filter in channel]

        logging.info('Expected channel list got from packages manifest:')
        self.print_list(all_channel_list)

        if len(channel_list) == 0:
            logging.error("Got 0 channel from packages manifest")
            logging.error("Test Failed - Got 0 channel from packages manifest.")
            exit(1)
        else:
            return channel_list

    def verify_channels(self, system_info, manifest_xml, username, password, current_arch, variant):
        # for now, this function can be only tested on RHEL6, as there is no param --available-channels on RHEL5
        logging.info("--------------- Begin to verify channel manifest ---------------")
        # get all channels which are not added
        available_channels = []
        cmd = "rhn-channel --available-channels --user=%s --password=%s" % (username, password)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get available channels with command rhn-channel...")
        if ret == 0:
            available_channels = output.splitlines()
        else:
            logging.error("Failed to get available channels.")

        # get all channels which are already added
        added_channels = []
        cmd = "rhn-channel --list --user=%s --password=%s" % (username, password)
        ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to get added channels with command rhn-channel...")
        if ret == 0:
            added_channels = output.splitlines()
        else:
            logging.error("Failed to get added channels.")

        channels_rhn = available_channels + added_channels

        # get all channels from manifest which are needed testing
        channels_manifest = self.get_channels_from_manifest(manifest_xml, current_arch, variant)
        list1 = self.cmp_arrays(channels_manifest, channels_rhn)
        if len(list1) > 0:
            logging.error("Failed to verify channel manifest.")
            logging.info('Below are channels in expected channel manifest but not in rhn-channel:')
            self.print_list(list1)
            logging.error("--------------- End to verify channel manifest: FAIL ---------------")
            logging.error("Test Failed - Failed to verify channel manifest.")
            exit(1)
        else:
            logging.info("All Expected channels exist in test list!")
            logging.info("--------------- End to verify channel manifest: PASS ---------------")
            return True

    def installation(self, system_info, manifest_xml, channel):
        logging.info("--------------- Begin to verify packages full installation for channel {0} ---------------".format(channel))
        # get packages from manifest
        package_list = RHNReadXML().get_package_list(manifest_xml, channel)
        logging.info("Packages need to install of channel {0}".format(package_list))
        logging.info(package_list)
        # There are source rpms in channels, but they can only be downloaded through the customer portal web site.  They aren't exposed to yum/yumdownloader/repoquery.
        # RHN APIs that can be used to query the source packages available, but the APIs are only available to RHN admins. So, let's not worry about SRPMs for now.
        # download source rpms from the customer portal web site - ignored for now

        # yum install binary packages
        result = True
        for pkg in package_list:
            cmd = "yum install -y %s" % pkg
            ret, output = RemoteSHH().run_cmd(system_info, cmd, "Trying to yum install package {0}".format(pkg))

            if ret == 0:
                if ("Complete!" in output) or ("Nothing to do" in output) or ("conflicts" in output):
                    logging.info("It's successful to install package %s." % pkg)
                else:
                    logging.error("Test Failed - Failed to install package %s of channel %s." % (pkg, channel))
                    result = False
            else:
                if "conflicts" in output:
                    logging.info("It's successful to install package %s." % pkg)
                else:
                    logging.error("Test Failed - Failed to install package %s of channel %s." % (pkg, channel))
                    result = False

                if result:
                    logging.info("--------------- End to verify packages full installation for channel {0}: PASS ---------------".format(channel))
                else:
                    logging.error("--------------- End to verify packages full installation for channel {0}: FAIL ---------------".format(channel))
        return result
