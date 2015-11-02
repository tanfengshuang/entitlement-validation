import os
import commands

RESOURCES_FILE = "RESOURCES.txt"
BEAKER_IP = "BEAKER_IP.properties"


# check if RESOURCES.txt exists, if yes, continue testing, otherwise, exit
if os.path.exists(RESOURCES_FILE):
    cmd = "cat RESOURCES.txt | grep EXISTING_NODES  | awk -F '=' '{print $2}'"
    print cmd
    ret, output = commands.getstatusoutput(cmd)
    if ret == 0 and "redhat.com" in output:
        print "Succeed to provision beaker system: {0}".format("output")
        commands.getstatusoutput("echo {0} > {1}".format(RESOURCES_FILE, BEAKER_IP))
    else:
        pass
else:
    print "Failed to download manifest!"
    exit(1)
