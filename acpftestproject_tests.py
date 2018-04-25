"""
This module contains automated tests that operate on the ACPFTestProject project.
"""

import unittest
from . import testprojectfixture


class ACPFTestProjectFixture(testprojectfixture.TestProjectFixture):
    """
    A fixture for tests that require a project with multiple
    internal and external packages.
    """
    def setUp(self):
        self.project = 'ACPFTestProject'
        self.repository = 'https://github.com/Knitschi/ACPFTestProject.git'
        super(ACPFTestProjectFixture, self).setUp()


    def test_pipeline_build_works(self):
        """
        Check that the pipeline target builds.
        """
        self.run_python_command('Sources/CPFBuildscripts/0_CopyScripts.py')
        self.run_python_command('1_Configure.py {0} --inherits {0}'.format(testprojectfixture.PARENT_CONFIG))
        self.run_python_command('2_Generate.py')
        self.run_python_command('3_Make.py --target pipeline')