#!/usr/bin/env python3
"""
This module contains automated tests that build one of the CPF test projects.
"""

import unittest
from pathlib import PureWindowsPath, PurePosixPath, PurePath

from Sources.CPFBuildscripts.python import miscosaccess
from Sources.CPFBuildscripts.python import filesystemaccess

BASE_TEST_DIR = ''
PARENT_CONFIG = ''

class ExcecuteCommandCase(unittest.TestCase):
    """
    This test case is used to test the execute_command_output() function.
    """

    
    #def test_execute_command(self):
    """
        This test should verify, that execute_command_output() works with recursive calls.
    """
    """
        self.osa = miscosaccess.MiscOsAccess()
        self.osa.execute_command_output('python -u -m Sources.CPFTests.Ping')
    """


class TestProjectFixture(unittest.TestCase):
    """
    This fixture clones a given repository into the clean directory in
    the BASE_TEST_DIR.
    """
    def setUp(self):
        self.fsa = filesystemaccess.FileSystemAccess()
        self.osa = miscosaccess.MiscOsAccess()

        # clone fresh project
        self.test_dir = PurePosixPath(BASE_TEST_DIR).joinpath(self.project)
        if self.fsa.exists(self.test_dir):
            self.fsa.rmtree(self.test_dir)
        self.fsa.mkdirs(BASE_TEST_DIR)
        self.osa.execute_command('git clone --recursive {0}'.format(self.repository), cwd=BASE_TEST_DIR)


    def run_python_command(self, argument):
        """
        The function runs python3 on Linux and python on Windows.
        """
        system = self.osa.system()
        if system == 'Windows':
            return self.osa.execute_command_output('python -u {0}'.format(argument), cwd=self.test_dir )
        elif system == 'Linux':
            return self.osa.execute_command_output('python3 -u {0}'.format(argument), cwd=self.test_dir )
        else:
            raise Exception('Unknown OS')



class SimpleOneLibCPFTestProjectFixture(TestProjectFixture):
    """
    A fixture that will do a fresh checkout of the ACPFTestProject.
    """
    def setUp(self):
        self.project = 'SimpleOneLibCPFTestProject'
        self.repository = 'https://github.com/Knitschi/SimpleOneLibCPFTestProject.git'
        super(SimpleOneLibCPFTestProjectFixture, self).setUp()

    
    def test_pipeline_build_works(self):
        """
        Check that the pipeline target builds with ACPFTestProject.
        """
        
        self.run_python_command('Sources/CPFBuildscripts/0_CopyScripts.py')
        self.run_python_command('1_Configure.py {0} --inherits {0}'.format(PARENT_CONFIG))
        self.run_python_command('2_Generate.py')
        self.run_python_command('3_Make.py --target pipeline')
        




        


