import logging

from Utils.RemoteSHH import RemoteSHH
from Utils.ParseManifestXML import ParseManifestXML
from Utils.EntitlementBase import EntitlementBase

class CDNVerification(EntitlementBase):
    def __init__(self):
        pass

    def check_registered(self, beaker_ip, beaker_username, beaker_password,):
        cmd = "subscription-manager identity"
        ret, output = RemoteSHH().run_cmd(beaker_ip, cmd, "Trying to check if registered to cdn...")
        if ret == 0:
            logging.info("The system is registered to server now.")
            return True
        else:
            logging.info("The system is not registered to server now.")
            return False


    def register(self, beaker_ip, beaker_username, beaker_password, username, password, subtype=""):
        if subtype == "":
            cmd = "subscription-manager register --username={0} --password='{1}'".format(username, password)
        else:
            cmd = "subscription-manager register --type={0} --username={1} --password='{2}'".format(subtype, username, password)

        if self.check_registered():
            logging.info("The system is already registered, need to unregister first!")
            cmd_unregister = "subscription-manager unregister"
            ret, output = RemoteSHH().run_cmd(beaker_ip, beaker_username, beaker_password, cmd_unregister, "Trying to unregister cdn server firstly...")

            if ret == 0:
                if ("System has been unregistered." in output) or ("System has been un-registered." in output):
                    logging.info("It's successful to unregister.")
                else:
                    logging.info("The system is failed to unregister, try to use '--force'!")
                    cmd += " --force"

        ret, output = RemoteSHH().run_cmd(beaker_ip, beaker_username, beaker_password, cmd, "Trying to register cdn server...")
        if ret == 0:
            if ("The system has been registered with ID:" in output) or ("The system has been registered with id:" in output):
                logging.info("It's successful to register.")
            else:
                logging.error("Test Failed - The information shown after registered is not correct.")
                exit(1)
        else:
            logging.error("Test Failed - Failed to register.")
            exit(1)

    def __parse_listavailable(self, output):
        datalines = output.splitlines()
        data_list = []

        # split output into segmentations for each pool
        data_segs = []
        segs = []
        tmpline = ""

        for line in datalines:
            if ("Product Name:" in line) or ("ProductName" in line) or ("Subscription Name" in line):
                 tmpline = line
            elif line and ":" not in line:
                tmpline = tmpline + ' ' + line.strip()
            elif line and ":" in line:
                segs.append(tmpline)
                tmpline = line
            if ("Machine Type:" in line) or ("MachineType:" in line) or ("System Type:" in line) or ("SystemType:" in line):
                segs.append(tmpline)
                data_segs.append(segs)
                segs = []

        for seg in data_segs:
            data_dict = {}
            for item in seg:
                keyitem = item.split(":")[0].replace(' ','')
                valueitem = item.split(":")[1].strip()
                data_dict[keyitem] = valueitem
            data_list.append(data_dict)

        return data_list

    def subscribe_pool(self, beaker_ip, beaker_username, beaker_password, poolid):
        cmd = "subscription-manager subscribe --pool={0}".format(poolid)
        ret, output = RemoteSHH().run_cmd(beaker_ip, beaker_username, beaker_password, cmd, "Trying to subscribe with poolid {0}".format(poolid))

        if ret == 0:
            #Note: the exact output should be as below:
            #For 6.2: "Successfully subscribed the system to Pool"
            #For 5.8: "Successfully consumed a subscription from the pool with id"
            if "Successfully " in output:
                logging.info("It's successful to subscribe.")
            else:
                logging.error("Test Failed - The information shown after subscribing is not correct.")
                exit(1)
        else:
            logging.error("Test Failed - Failed to subscribe.")
            exit(1)
