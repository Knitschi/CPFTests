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
    def setUp(self):
        self.project = 'BCPFTestProject'
        self.repository = 'https://github.com/Knitschi/BCPFTestProject.git'
        super(BCPFTestProjectFixture, self).setUp()

   
    def test_pipeline_works(self):
        """
        Check that the pipeline target builds.
        """
        # Setup
        self.generate_project()

        # Test the pipeline works
        self.build_target('pipeline')
