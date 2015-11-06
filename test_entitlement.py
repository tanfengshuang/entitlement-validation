import unittest

from Tests import *

# Create our test suite.
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(CDN_Entitlement_33('test_CDN_Entitlement'))
    suite.addTest(CDN_Entitlement_22('test_CDN_Entitlement'))
    suite.addTest(CDN_Entitlement_11('test_CDN_Entitlement'))
    return suite

# Launch our test suite
if __name__ == '__main__':
    suite = test_suite()
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
