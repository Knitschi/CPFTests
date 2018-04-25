"""
This module contains automated tests that operate on the SimpleOneLibCPFTestProject project.
"""

import unittest
from . import testprojectfixture


############################################################################################
class SimpleOneLibCPFTestProjectFixture(testprojectfixture.TestProjectFixture):
    """
    A fixture for tests that can be done with a minimal project that has no test executable and 
    only a library package.
    """
    def setUp(self):
        self.project = 'SimpleOneLibCPFTestProject'
        self.repository = 'https://github.com/Knitschi/SimpleOneLibCPFTestProject.git'
        super(SimpleOneLibCPFTestProjectFixture, self).setUp()

    
    def test_target_builds_work(self):
        """
        Check that the pipeline target builds.
        """
        # pipeline build
        self.run_python_command('Sources/CPFBuildscripts/0_CopyScripts.py')
        self.run_python_command('1_Configure.py {0} --inherits {0}'.format(testprojectfixture.PARENT_CONFIG))
        self.run_python_command('2_Generate.py')
        self.run_python_command('3_Make.py --target pipeline')

        # versionCompatibilityChecks should not be available
        self.assertRaisesRegex(self.run_python_command('3_Make.py --target versionCompatibilityChecks'), 'bla')