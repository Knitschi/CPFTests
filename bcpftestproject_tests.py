"""
This module contains automated tests that operate on the BCPFTestProject project.
"""

import unittest
from . import testprojectfixture


class BCPFTestProjectFixture(testprojectfixture.TestProjectFixture):
    """
    A fixture for tests that require a project with multiple
    internal library packages.
    """

    cpf_root_dir = ''
    project = ''

    @classmethod
    def setUpClass(cls):
        cls.project = 'BCPFTestProject'
        cls.cpf_root_dir = testprojectfixture.prepareTestProject('https://github.com/Knitschi/BCPFTestProject.git', cls.project)


    def setUp(self):
        super(BCPFTestProjectFixture, self).setUp(self.project, self.cpf_root_dir)  


    def test_pipeline_works(self):
        """
        Check that the pipeline target builds.
        """
        # Setup
        self.generate_project()

        # Test the pipeline works
        self.build_target('pipeline')
