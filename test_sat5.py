import unittest

from SAT5.Tests.SAT5Entitlement import SAT5Entitlement


# Create our test suite.
def rhn_suite():
    suite = unittest.TestSuite()
    suite.addTest(SAT5Entitlement('testSAT5Entitlement_VARIANT_ARCH'))
    return suite

# Launch our test suite
if __name__ == '__main__':
    # python test_rhn.py
    # suite = rhn_suite()
    # runner = unittest.TextTestRunner()
    # result = runner.run(suite)

    # nosetests test_rhn.py
    rhn_suite()


