#!/usr/bin/python3
"""
This module contains a testcase class the can be used to run tests
on a cpf test project.
"""

import os
import unittest
from pathlib import PurePosixPath
import shutil

from Sources.CPFBuildscripts.python import miscosaccess
from Sources.CPFBuildscripts.python import filesystemaccess
from Sources.CPFBuildscripts.python import filelocations


BASE_TEST_DIR = ''
PARENT_CONFIG = ''


class TestProjectFixture(unittest.TestCase):
    """
    This fixture clones a given repository into the clean directory in
    the BASE_TEST_DIR.
    It will also change the CPFCMake and CPFBuildscripts submodules to the ones
    in the locally checked out and run CMakeProjectFramework repository.
    """
    def setUp(self):

        # add a big fat line to help with manual output parsing when an error occurs.
        print('-- Run test: {0} - {1} '.format(self.project,self._testMethodName))

        self.fsa = filesystemaccess.FileSystemAccess()
        self.osa = miscosaccess.MiscOsAccess()

        # clone fresh project
        self.test_dir = PurePosixPath(BASE_TEST_DIR).joinpath(self.project)
        if self.fsa.exists(self.test_dir):
            # we remove remaining testfiles at the beginning of a test, so we
            # have the project still available for debugging if the test fails.
            self.fsa.rmtree(self.test_dir)
        self.fsa.mkdirs(BASE_TEST_DIR)
        self.osa.execute_command_output('git clone --recursive {0}'.format(self.repository), cwd=BASE_TEST_DIR, print_output=miscosaccess.OutputMode.ON_ERROR)
        
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
        shutil.copytree(str(this_package_dir), str(test_project_package_dir))
        # We also commit the changes to make sure the repository is not dirty
        # which is expected after a "fresh" checkout.
        self.osa.execute_command_output('git commit --allow-empty . -m "Set package content to local developer files."', cwd=test_project_package_dir, print_output=miscosaccess.OutputMode.ON_ERROR)
        self.osa.execute_command_output('git commit --allow-empty . -m "Update {0}"'.format(package), cwd=self.test_dir, print_output=miscosaccess.OutputMode.ON_ERROR)


    def run_python_command(self, argument, print_output=miscosaccess.OutputMode.ON_ERROR, print_command=False):
        """
        The function runs python3 on Linux and python on Windows.
        """
        system = self.osa.system()
        if system == 'Windows':
            return self.osa.execute_command_output(
                'python -u {0}'.format(argument), 
                cwd=self.test_dir, 
                print_output=print_output, 
                print_command=print_command 
                )
        elif system == 'Linux':
            # Force english language via environment variable,
            # so we can parse the output reliably.
            environment = os.environ
            environment['LANG'] = "en_US.UTF-8" 
            return self.osa.execute_command_output(
                'python3 -u {0}'.format(argument),
                cwd=self.test_dir,
                print_output=print_output,
                print_command=print_command,
                env=environment 
                )
        else:
            raise Exception('Unknown OS')


    def is_visual_studio_config(self):
        return PARENT_CONFIG == 'VS2017-shared' or PARENT_CONFIG == 'VS2017-static'

    def is_linux_debug_config(self):
        return PARENT_CONFIG == 'Gcc-shared-debug' or PARENT_CONFIG == 'Clang-shared-debug'

    def is_clang_config(self):
        return PARENT_CONFIG == 'Clang-static-release' or PARENT_CONFIG == 'Clang-shared-debug'

    def is_make_config(self):
        return PARENT_CONFIG == 'Clang-shared-debug'or PARENT_CONFIG == 'Gcc-shared-debug'

    def is_ninja_config(self):
        return PARENT_CONFIG == 'Clang-static-release'

    def is_make_config(self):
        return PARENT_CONFIG == 'Gcc-shared-debug' or PARENT_CONFIG == 'Clang-shared-debug'

    def is_msvc_or_debug_config(self):
        return self.is_visual_studio_config() or self.is_linux_debug_config()

    def assert_targets_build(self, targets):
        for target in targets:
            command = '3_Make.py --target {0}'.format(target)
            print(command) # We do our own abbreviated command printing here.
            self.run_python_command(command)


    def build_target(self, target, config=None):
        command = '3_Make.py --target {0}'.format(target)
        if config:
            command += ' --config {0}'.format(config)
        print(command) # We do our own abbreviated command printing here.
        outputlist = self.run_python_command(command)
        return '\n'.join(outputlist)


    def assert_targets_do_not_exist(self, targets):
        
        target_misses_signature = ''
        if self.is_visual_studio_config():
            target_misses_signature = 'MSBUILD : error MSB1009:'
        elif self.is_make_config():
            target_misses_signature = '*** No rule to make target'
        elif self.is_ninja_config():
            target_misses_signature = 'ninja: error: unknown target'
        else:
            raise Exception('Error! Missing case for current buildtool.')
        
        for target in targets:
            with self.assertRaises(miscosaccess.CalledProcessError) as cm:
                # The reason to not print the output of the failing call ist, that MSBuild seems to parse
                # its own output to determine if an error happened. When a nested MSBuild call fails, the
                # parent call itself will also fail even if the nested call was supposed to fail like here.
                command = '3_Make.py --target {0}'.format(target)
                print(command) # We do our own abbreviated command printing here.
                self.run_python_command(command, print_output=miscosaccess.OutputMode.NEVER)
            # error MSB1009 says that a project is missing, which means the target does not exist.
            self.assertIn(target_misses_signature, cm.exception.stdout)


    def generate_project(self):
        """
        Setup helper that runs all steps up to the generate step.
        """
        self.run_python_command('Sources/CPFBuildscripts/0_CopyScripts.py')
        self.run_python_command('1_Configure.py {0} --inherits {0}'.format(PARENT_CONFIG))
        self.run_python_command('2_Generate.py')

