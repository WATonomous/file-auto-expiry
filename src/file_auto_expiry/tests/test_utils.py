import unittest
import os
import sys
from unittest.mock import MagicMock, patch
module_path = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

from ..utils.interface import *
from ..utils.expiry_checks import *

class TestUtils(unittest.TestCase):
    @patch("pwd.getpwuid")
    @patch("os.stat")
    def test_get_file_creator(self, patch_stat, patch_pwd):
        """
        Tests retrieving the user name of a file owner
        """
        # Successfully retrieves file owner
        patch_stat.return_value.st_uid=5111
        patch_stat.return_value.st_gid=1555
        patch_pwd.return_value.pw_name="tester_account"

        file_creator = get_file_creator("/home/machung/test.txt")
        self.assertEqual(file_creator[0], "tester_account")
        self.assertEqual(file_creator[1], 5111)
        self.assertEqual(file_creator[2], 1555)
        
    @patch('os.stat')
    def test_is_expired_filepath(self, patch_stat):
        """
        Tests the is_expired_file function
        """
        time_for_expiry = 30 # 30 days
        patch_stat.st_atime = 5 # 5 days
        patch_stat.st_ctime = 5 # 5 days
        patch_stat.st_mtime = 5 # 5 days
        scrape_time = 50  # 50 days
        expiry_threshold = scrape_time - time_for_expiry

        # Days since last access is 5 < 20
        # The file should be expired
        self.assertTrue(is_expired_filepath("test_name.txt", patch_stat, expiry_threshold)[0])

        expiry_threshold = -20  # change to 10 days
        # Days since last access is 5 > -20
        # The file should not be expired
        expiry_test_result =  is_expired_filepath("test_name.txt", patch_stat, expiry_threshold)
        self.assertFalse(expiry_test_result[0])
        self.assertTrue(5, expiry_test_result[2])
        self.assertTrue(5, expiry_test_result[3])
        self.assertTrue(5, expiry_test_result[4])

if __name__ == '__main__':
    unittest.main()