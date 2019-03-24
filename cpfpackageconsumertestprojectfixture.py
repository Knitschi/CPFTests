"""
This module contains a TestProjectFixture for the CPFPackageConsumerTestProject.
"""


import unittest
from . import testprojectfixture



class CPFPackageConsumerTestProjectFixture(testprojectfixture.TestProjectFixture):
    """
    A fixture for testing for consuming the binary package of the SimpleOneLibCPFTestProject.
    """

    cpf_root_dir = ''
    project = ''

    @classmethod
    def setUpClass(cls, instantiating_test_module=__name__.split('.')[-1]):
        cls.instantiating_module = instantiating_test_module
        cls.project = 'CPFPackageConsumerTestProject'
        cls.cpf_root_dir = testprojectfixture.prepareTestProject('https://github.com/Knitschi/CPFPackageConsumerTestProject.git', cls.project, instantiating_test_module)


    def setUp(self):
        super(CPFPackageConsumerTestProjectFixture, self).setUp(self.project, self.cpf_root_dir, self.instantiating_module)

