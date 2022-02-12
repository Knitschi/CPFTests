"""
This module contains automated tests that operate on the BCPFTestProject project.
"""

import unittest
import sys
from . import testprojectfixture


class BCPFTestProjectFixture(testprojectfixture.TestProjectFixture):
    """
    A fixture for tests that require a project with multiple
    internal library packages.
    """

    cpf_root_dir = ''
    cpf_cmake_dir = 'Sources/CPFCMake'
    ci_buildconfigurations_dir = 'Sources/CIBuildConfigurations'
    project = ''

    @classmethod
    def setUpClass(cls, instantiating_test_module=__name__.split('.')[-1]):
        cls.instantiating_module = instantiating_test_module
        cls.project = 'BCPFTestProject'
        cls.cpf_root_dir = testprojectfixture.prepareTestProject('https://github.com/Knitschi/BCPFTestProject.git', cls.project, instantiating_test_module)


    def setUp(self):
        super(BCPFTestProjectFixture, self).setUp(self.project, self.cpf_root_dir, self.cpf_cmake_dir, self.ci_buildconfigurations_dir, self.instantiating_module)  


    def test_pipeline_works(self):
        """
        Check that the pipeline target builds.
        """
        # Setup
        self.generate_project()

        # Test the pipeline works
        self.build_target('pipeline')
