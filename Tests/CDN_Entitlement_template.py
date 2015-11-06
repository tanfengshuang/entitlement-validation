import unittest

pid = "PID"

class CDN_Entitlement_PID(unittest.TestCase):

    def setUp(self):
        print "Setup..."

    def test_CDN_Entitlement(self):
        print "test_CDN_Entitlement"
        #register("stage_test_12", "redhat")

    def tearDown(self):
        print "tearDown..."

if __name__ == '__main__':
    unittest.main()