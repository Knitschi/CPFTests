#!/usr/bin/env python3
"""
This module contains automated tests that build one of the CPF test projects.
"""

import unittest
from pathlib import PureWindowsPath, PurePosixPath, PurePath
import shutil

from Sources.CPFBuildscripts.python import miscosaccess
from Sources.CPFBuildscripts.python import filesystemaccess
from Sources.CPFBuildscripts.python import filelocations


BASE_TEST_DIR = ''
PARENT_CONFIG = ''

class ExcecuteCommandCase(unittest.TestCase):
    """
    This test case is used to test the execute_command_output() function.
    """

    def test_execute_command(self):
        """
        This test should verify, that execute_command_output() works with recursive calls.
        """
        self.osa = miscosaccess.MiscOsAccess()
        self.osa.execute_command_output('python -u -m Sources.CPFTests.ping')


class TestProjectFixture(unittest.TestCase):
    """
    This fixture clones a given repository into the clean directory in
    the BASE_TEST_DIR.
    It will also change the CPFCMake and CPFBuildscripts submodules to the ones
    in the locally checked out and run CMakeProjectFramework repository.
    """
    def setUp(self):
        self.fsa = filesystemaccess.FileSystemAccess()
        self.osa = miscosaccess.MiscOsAccess()

        # clone fresh project
        self.test_dir = PurePosixPath(BASE_TEST_DIR).joinpath(self.project)
        if self.fsa.exists(self.test_dir):
            # we remove remaining testfiles at the beginning of a test, so we
            # have the project still available for debugging if the test fails.
            self.fsa.rmtree(self.test_dir)
        self.fsa.mkdirs(BASE_TEST_DIR)
        self.osa.execute_command_output('git clone --recursive {0}'.format(self.repository), cwd=BASE_TEST_DIR)
        
        # Replace the CPFCMake and CPFBuildscripts packages in the test project with the ones
        # that are used by this repository. This makes sure that we test the versions that
        # are used here and not the ones that are set in the test project.
        self.replace_package_in_test_project_with_local('CPFCMake')
        self.replace_package_in_test_project_with_local('CPFBuildscripts')


    def replace_package_in_test_project_with_local(self, package):
        """
        This function replaces a package in the cpf project situated at test_project_root_dir
        with the package of same name in this repository.
        """
        this_root_dir = PurePosixPath(filelocations.get_cpf_root_dir_from_script_dir())
        rel_package_path = 'Sources/{0}'.format(package)
        this_package_dir = this_root_dir.joinpath(rel_package_path)
        test_project_package_dir = self.test_dir.joinpath(rel_package_path)

        # We delete the package in the the copy the content of this package over
        self.fsa.rmtree(test_project_package_dir)
        shutil.copytree(this_package_dir, test_project_package_dir)
        # We also commit the changes to make sure the repository is not dirty
        # which is expected after a "fresh" checkout.
        self.osa.execute_command('git commit --allow-empty . -m "Set package content to local developer files."', cwd=test_project_package_dir)
        self.osa.execute_command('git commit --allow-empty . -m "Update {0}"'.format(package), cwd=self.test_dir)


    def run_python_command(self, argument):
        """
        The function runs python3 on Linux and python on Windows.
        """
        system = self.osa.system()
        if system == 'Windows':
            print('----------------------------------------------')
            print(str(self.test_dir))
            return self.osa.execute_command_output('python -u {0}'.format(argument), cwd=self.test_dir )
        elif system == 'Linux':
            return self.osa.execute_command_output('python3 -u {0}'.format(argument), cwd=self.test_dir )
        else:
            raise Exception('Unknown OS')



class SimpleOneLibCPFTestProjectFixture(TestProjectFixture):
    """
    A fixture for tests that can be done with a minimal project that has no test executable and 
    only a library package.
    """
    def setUp(self):
        self.project = 'SimpleOneLibCPFTestProject'
        self.repository = 'https://github.com/Knitschi/SimpleOneLibCPFTestProject.git'
        super(SimpleOneLibCPFTestProjectFixture, self).setUp()

    
    def test_pipeline_build_works(self):
        """
        Check that the pipeline target builds.
        """
        self.run_python_command('Sources/CPFBuildscripts/0_CopyScripts.py')
        self.run_python_command('1_Configure.py {0} --inherits {0}'.format(PARENT_CONFIG))
        self.run_python_command('2_Generate.py')
        self.run_python_command('3_Make.py --target pipeline')


class ACPFTestProjectFixture(TestProjectFixture):
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
        self.run_python_command('1_Configure.py {0} --inherits {0}'.format(PARENT_CONFIG))
        self.run_python_command('2_Generate.py')
        self.run_python_command('3_Make.py --target pipeline')


class BCPFTestProjectFixture(TestProjectFixture):
    """
    A fixture for tests that require a project with multiple
    internal library packages.
    """
    def setUp(self):
        self.project = 'BCPFTestProject'
        self.repository = 'https://github.com/Knitschi/BCPFTestProject.git'
        super(BCPFTestProjectFixture, self).setUp()

   
    def test_pipeline_build_works(self):
        """
        Check that the pipeline target builds.
        """
        self.run_python_command('Sources/CPFBuildscripts/0_CopyScripts.py')
        self.run_python_command('1_Configure.py {0} --inherits {0}'.format(PARENT_CONFIG))
        self.run_python_command('2_Generate.py')
        self.run_python_command('3_Make.py --target pipeline')


        


