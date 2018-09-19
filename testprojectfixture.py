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
COMPILER_CONFIG = ''


def prepareTestProject(repository, project):
    """
    This method clones a given repository of a CPF test project into the testdirectory 
    that is stored in the global BASE_TEST_DIR variable. After that it copies the
    current versions of CPFCMake and CPFBuildscripts into the test project, to make
    sure that the tests test the code that comes with this repository and not the
    the versions that are included in the test projects.

    To save time, test projects are only cloned once for all tests.
    All source files in the test project should be left unchanged to
    prevent coupling of single tests. All Generated files are deleted
    before each test, so they can be changed by test cases.
    """

    print('-- Prepare test-project: {0}'.format(project))

    fsa = filesystemaccess.FileSystemAccess()
    osa = miscosaccess.MiscOsAccess()

    # clone fresh project
    cpf_root_dir = PurePosixPath(BASE_TEST_DIR).joinpath(project)
    if fsa.exists(cpf_root_dir):
        # we remove remaining testfiles at the beginning of a test, so we
        # have the project still available for debugging if the test fails.
        fsa.rmtree(cpf_root_dir)
    fsa.mkdirs(BASE_TEST_DIR)
    osa.execute_command_output('git clone --recursive {0}'.format(repository), cwd=BASE_TEST_DIR, print_output=miscosaccess.OutputMode.ON_ERROR)
    
    # Replace the CPFCMake and CPFBuildscripts packages in the test project with the ones
    # that are used by this repository. This makes sure that we test the versions that
    # are used here and not the ones that are set in the test project.
    replace_package_in_test_project_with_local('CPFCMake', cpf_root_dir)
    replace_package_in_test_project_with_local('CPFBuildscripts', cpf_root_dir)
    return cpf_root_dir


def replace_package_in_test_project_with_local(package, cpf_root_dir):
    """
    This function replaces a package in the cpf project situated at test_project_root_dir
    with the package of same name in this repository.
    """
    fsa = filesystemaccess.FileSystemAccess()
    osa = miscosaccess.MiscOsAccess()

    this_root_dir = PurePosixPath(filelocations.get_cpf_root_dir_from_script_dir())
    rel_package_path = 'Sources/{0}'.format(package)
    this_package_dir = this_root_dir.joinpath(rel_package_path)
    test_project_package_dir = cpf_root_dir.joinpath(rel_package_path)

    # We delete the package in the the copy the content of this package over
    fsa.rmtree(test_project_package_dir)
    shutil.copytree(str(this_package_dir), str(test_project_package_dir))
    # We also commit the changes to make sure the repository is not dirty
    # which is expected after a "fresh" checkout.
    osa.execute_command_output('git commit --allow-empty . -m "Set package content to local developer files."', cwd=test_project_package_dir, print_output=miscosaccess.OutputMode.ON_ERROR)
    osa.execute_command_output('git commit --allow-empty . -m "Update {0}"'.format(package), cwd=cpf_root_dir, print_output=miscosaccess.OutputMode.ON_ERROR)



class TestProjectFixture(unittest.TestCase):
    """
    This fixture offers utilities for tests that work on checked out test projects.
    """

    def setUp(self, project, cpf_root_dir):

        self.fsa = filesystemaccess.FileSystemAccess()
        self.osa = miscosaccess.MiscOsAccess()

        self.project = project
        self.cpf_root_dir = cpf_root_dir
        self.locations = filelocations.FileLocations(cpf_root_dir)

        # add a big fat line to help with manual output parsing when an error occurs.
        if str(self._testMethodName) != "runTest":
            print('-- Run test: {0}'.format(self._testMethodName))


    def generate_project(self, d_options=[]):
        """
        Setup helper that runs all steps up to the generate step.
        Previously existing configurations or generated files are deleted.
        """
        self.cleanup_generated_files()

        self.run_python_command('Sources/CPFBuildscripts/0_CopyScripts.py')
        d_option_string = ''
        for option in d_options:
            d_option_string += '-D ' + option + ' '

        self.run_python_command('1_Configure.py {0} --inherits {0} {1}'.format(PARENT_CONFIG, d_option_string))
        command = '2_Generate.py {0}'.format(PARENT_CONFIG)
        print(command)
        self.run_python_command(command)


    def cleanup_generated_files(self):
        # We delete all generated files to make sure they do not interfere with the test case.
        config_dir = self.cpf_root_dir.joinpath('Configuration')
        if self.fsa.exists(config_dir):
            self.fsa.rmtree(config_dir)

        generated_dir = self.cpf_root_dir.joinpath('Generated')
        if self.fsa.exists(generated_dir):
            self.fsa.rmtree(generated_dir)

    def run_python_command(self, argument, print_output=miscosaccess.OutputMode.ON_ERROR, print_command=False):
        """
        The function runs python3 on Linux and python on Windows.
        """
        system = self.osa.system()
        if system == 'Windows':
            return self.osa.execute_command_output(
                'python -u {0}'.format(argument), 
                cwd=self.cpf_root_dir, 
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
                cwd=self.cpf_root_dir,
                print_output=print_output,
                print_command=print_command,
                env=environment 
                )
        else:
            raise Exception('Unknown OS')


    def is_visual_studio_config(self):
        return PARENT_CONFIG == 'VS2017-shared' or PARENT_CONFIG == 'VS2017-static'

    def is_debug_compiler_config(self):
        return COMPILER_CONFIG == 'Debug'

    def is_linux_debug_config(self):
        return PARENT_CONFIG == 'Gcc-shared-debug' or PARENT_CONFIG == 'Clang-shared-debug'

    def is_clang_config(self):
        return PARENT_CONFIG == 'Clang-static-release' or PARENT_CONFIG == 'Clang-shared-debug'

    def is_make_config(self):
        return PARENT_CONFIG == 'Clang-shared-debug' or PARENT_CONFIG == 'Gcc-shared-debug'

    def is_ninja_config(self):
        return PARENT_CONFIG == 'Clang-static-release'

    def is_make_config(self):
        return PARENT_CONFIG == 'Gcc-shared-debug' or PARENT_CONFIG == 'Clang-shared-debug'

    def is_msvc_or_debug_config(self):
        return self.is_visual_studio_config() or self.is_linux_debug_config()

    def is_windows(self):
        return self.osa.system() == 'Windows'

    def is_linux(self):
        return self.osa.system() == 'Linux'

    def is_shared_libraries_config(self):
        return PARENT_CONFIG == 'Gcc-shared-debug' or PARENT_CONFIG == 'Clang-shared-debug' or PARENT_CONFIG == 'VS2017-shared'

    def get_compiler_configs(self):
        buildTypeKey = "CMAKE_BUILD_TYPE"                       # This should be defined for single config generators.
        configurationTypeKey = "CMAKE_CONFIGURATION_TYPES"      # This should be defined for multi config generators.
        
        # Get the values for both variables
        variableValues = self.get_cache_variable_values([configurationTypeKey, buildTypeKey])
        
        configValues = []
        if buildTypeKey in variableValues:
            assert(variableValues[buildTypeKey])                # It should have a value when it is defined.
            assert(configurationTypeKey not in variableValues)  # Only one of both should be defined.
            return variableValues[buildTypeKey]
        else:
            assert(configurationTypeKey in variableValues)
            return variableValues[configurationTypeKey].split(";")

    def get_cache_variable_values(self, variables):
        build_dir = self.locations.get_full_path_config_makefile_folder(PARENT_CONFIG)
        allVariables = self.osa.execute_command_output(
            'cmake -LA -N',
            cwd=build_dir,
            print_output=miscosaccess.OutputMode.ON_ERROR,
            print_command=False
        )
        
        variableValueMap = {} 
        for line in allVariables:
            for variable in variables:
                if variable in line:
                    splitLine = line.split('=')
                    if len(splitLine) > 1:
                        variableValueMap[variable] = splitLine[1]
                    else:
                        variableValueMap[variable] = ""

        return variableValueMap

    def get_package_version(self, package):
        package_dir = self.cpf_root_dir.joinpath('Sources/{0}'.format(package))
        script = self.cpf_root_dir.joinpath('Sources/CPFCMake/Scripts/getVersionFromRepository.cmake')
        return self.osa.execute_command_output(
            'cmake -DREPO_DIR="{0}" -P {1}'.format(package_dir, script),
            cwd=self.cpf_root_dir,
            print_output=miscosaccess.OutputMode.ON_ERROR,
            print_command=False
        )[0]

    def build_targets(self, targets):
        for target in targets:
            self.build_target(target)

    def build_target(self, target, config=None ):
        command = '3_Make.py --target {0}'.format(target)
        if self.is_visual_studio_config():
            if config:
                command += ' --config {0}'.format(config)
            else:
                command += ' --config {0}'.format(COMPILER_CONFIG)
        print(command) # We do our own abbreviated command printing here.
        outputlist = self.run_python_command(command)
        return '\n'.join(outputlist)

    
    def assert_target_does_not_exist(self, target):
        target_misses_signature = ''
        if self.is_visual_studio_config():
            target_misses_signature = 'MSBUILD : error MSB1009:'
        elif self.is_make_config():
            target_misses_signature = '*** No rule to make target'
        elif self.is_ninja_config():
            target_misses_signature = 'ninja: error: unknown target'
        else:
            raise Exception('Error! Missing case for current buildtool.')
        
        with self.assertRaises(miscosaccess.CalledProcessError) as cm:
            # The reason to not print the output of the failing call ist, that MSBuild seems to parse
            # its own output to determine if an error happened. When a nested MSBuild call fails, the
            # parent call itself will also fail even if the nested call was supposed to fail like here.
            command = '3_Make.py --target {0}'.format(target)
            print(command) # We do our own abbreviated command printing here.
            self.run_python_command(command, print_output=miscosaccess.OutputMode.NEVER)
        # error MSB1009 says that a project is missing, which means the target does not exist.
        if not target_misses_signature in cm.exception.stdout:
            raise Exception('Test Error! Target {0} should not exist, but it did.'.format(target))
        

    def assert_targets_do_not_exist(self, targets):
        for target in targets:
            self.assert_target_does_not_exist(target)


    def assert_output_contains_signature(self, output, target, signature, trigger_source_file = None):
        """
        Builds the target and looks for the signature in its output.
        If the signature is not int the output it raises an exception.
        """
        missing_strings = self.find_missing_signature_strings(output, signature)
        if missing_strings:
            self.print_build_output(output)
            error_string= 'Test Error! Signature parts "{0}" were NOT found in build output of target {1}.'.format(missing_strings, target)
            if trigger_source_file:
                error_string = 'The build of target {0} was not triggered by touching file "{1}". The file does not seem to be one of the targets dependencies.'.format(target, trigger_source_file)
            raise Exception(error_string)

    def print_build_output(self, output):
        print('------------------------- Start test-build output ------------------')
        print(output)
        print('------------------------- End test-build output ------------------')

    def assert_output_has_not_signature(self, output, target, signature):
        """
        Builds the given target and raises an exception if the given signature
        can be found in the build output.
        """
        missing_strings = self.find_missing_signature_strings(output, signature)
        if not missing_strings:
            self.print_build_output(output)
            raise Exception('Test Error! Signature "{0}" was found in build output of target {1}.'.format(signature, target) )


    def find_missing_signature_strings(self, output, signature):
        missing_strings = []
        for string in signature:
            if not string in output:
                missing_strings.append(string)
        return missing_strings


    def assert_target_output_files_exist(self, target, files):
        """
        File pathes must be relative to CMAKE_BINARY_DIR.
        """
        missing_files = []
        for file in files:
            full_file = self.cpf_root_dir.joinpath('Generated').joinpath(PARENT_CONFIG).joinpath(file)
            if not self.fsa.exists(full_file):
                missing_files.append(str(file))
        if missing_files:
            raise Exception('Test error! The following files were not produced by target {0} as expected: {1}'.format(target, '; '.join(missing_files)))


    def assert_target_does_not_create_files(self, target, files ):
        """
        Throws an exception if the given files exist. 
        File pathes must be relative to CMAKE_BINARY_DIR or full pathes.
        """
        existing_files = []
        for file in files:
            full_file = file
            if not os.path.isabs(full_file):
                full_file = self.cpf_root_dir.joinpath('Generated').joinpath(PARENT_CONFIG).joinpath(file)

            if self.fsa.exists(full_file):
                existing_files.append(str(full_file))

        if existing_files:
            raise Exception('Test error! The following files were unexpectedly produced by target {0}: {1}'.format(target, '; '.join(existing_files)))

