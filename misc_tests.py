"""
This module contains automated tests that do not fit into any other file.
"""

import unittest
from Sources.CPFBuildscripts.python import miscosaccess

class ExcecuteCommandCase(unittest.TestCase):
    """
    This test case is used to test the execute_command_output() function.
    """

    def test_execute_command(self):
        """
        This test should verify, that execute_command_output() works with recursive calls.
        """
        self.osa = miscosaccess.MiscOsAccess()
        self.osa.execute_command_output('python -u -m Sources.CPFTests.ping')