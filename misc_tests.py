"""
This module contains automated tests that do not fit into any other file.
"""

import unittest
from Sources.CPFBuildscripts.python import miscosaccess

class ExecuteCommandCase(unittest.TestCase):
    """
    This test case is used to test the execute_command_output() function.
    """

    def setUp(self):
        # add a big fat line to help with manual output parsing when an error occurs.
        printWithModulePrefix('Run test: {0}'.format(self._testMethodName))

    def test_execute_command(self):
        """
        This test should verify, that execute_command_output() works with recursive calls.
        """
        osa = miscosaccess.MiscOsAccess()
        system = osa.system()
        if system == 'Windows':
            return osa.execute_command_output('python -u -m Sources.CPFTests.ping')
        elif system == 'Linux':
            return osa.execute_command_output('python3 -u -m Sources.CPFTests.ping')
        else:
            raise Exception('Unknown OS')


def printWithModulePrefix(string):
    print('[' + __name__.split('.')[-1]  + '] ' + string)