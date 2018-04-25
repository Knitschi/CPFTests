"""
This module contains automated tests that operate on the SimpleOneLibCPFTestProject project.
"""

import unittest
import os
import pprint

from Sources.CPFBuildscripts.python import miscosaccess

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

        # versionCompatibilityChecks should not be available on visual studio solutions
        if self.is_visual_studio_config():
            with self.assertRaises(miscosaccess.CalledProcessError) as cm:
                # The reason to not print the output of the failing call ist, that MSBuild seems to parse
                # its own output to determine if an error happened. When a nested MSBuild call fails, the
                # parent call itself will also fail even if the nested call was supposed to fail like here.
                self.run_python_command('3_Make.py --target versionCompatibilityChecks', print_output=miscosaccess.OutputMode.NEVER)
            # error MSB1009 says that a project is missing, which means the target does not exist.
            self.assertIn('MSBUILD : error MSB1009:', cm.exception.stdout)




