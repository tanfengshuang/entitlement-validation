import os
import time
import logging
import unittest

from Tests import *
from Utils.environment import *

def log_setting(variant, arch, rhn):
    # write log into specified files
    path = './log/'
    if not os.path.exists(path):
        os.mkdir(path)
    filename = "{0}{1}-{2}-{3}-{4}.log".format(path, variant, arch, rhn, time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime(time.time())))
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)5s|%(filename)22s:%(lineno)4d|: %(message)s',
                        datefmt='%d %b %Y %H:%M:%S'
                        )
    nor = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s %(levelname)5s|%(filename)18s:%(lineno)3d|: %(message)s')
    filehandler = logging.FileHandler(filename)
    filehandler.suffix = "%Y-%m-%d"
    filehandler.setFormatter(formatter)
    nor.addHandler(filehandler)

# Create our test suite.
def cdn_suite():
    log_setting(variant, arch, rhn)
    suite = unittest.TestSuite()
    suite.addTest(CDNEntitlement_69('testCDNEntitlement'))
    return suite

# Launch our test suite
if __name__ == '__main__':
    log_setting(variant, arch, rhn)
    #cdn_suite()
    suite = cdn_suite()
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
