import unittest
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)5s|%(filename)22s:%(lineno)4d|%(threadName)s|: %(message)s',
    datefmt='%d %b %Y %H:%M:%S'
    )

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


