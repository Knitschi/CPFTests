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


    def test_pipeline_works(self):
        """
        Check that the pipeline target builds.
        """
        # Setup
        self.generate_project()

        # Test the pipeline works
        self.build_target('pipeline')
