import unittest


# Create our test suite.
def cdn_suite():
    suite = unittest.TestSuite()
    return suite

# Launch our test suite
if __name__ == '__main__':
    # python test_cdn.py
    # suite = cdn_suite()
    # runner = unittest.TextTestRunner()
    # result = runner.run(suite)

    # nosetests test_cdn.py
    cdn_suite()


