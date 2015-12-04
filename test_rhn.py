import unittest

from Tests.RHNEntitlement import RHNEntitlement


# Create our test suite.
def rhn_suite():
    suite = unittest.TestSuite()
    suite.addTest(RHNEntitlement('testRHNEntitlement'))
    return suite

# Launch our test suite
if __name__ == '__main__':
    # python test_rhn.py
    # suite = rhn_suite()
    # runner = unittest.TextTestRunner()
    # result = runner.run(suite)

    # nosetests test_rhn.py
    rhn_suite()


