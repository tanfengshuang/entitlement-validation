import unittest

from Tests import *

# Create our test suite.
def test_suite():
    suite = unittest.TestSuite()
    return suite

# Launch our test suite
if __name__ == '__main__':
    suite = test_suite()
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
