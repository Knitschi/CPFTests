"""
This module contains automated tests that operate on the ACPFTestProject project.
"""

import unittest
import sys
import pprint
from . import testprojectfixture
from pathlib import PureWindowsPath, PurePosixPath, PurePath

from Sources.CPFBuildscripts.python import miscosaccess


class ACPFTestProjectFixture(testprojectfixture.TestProjectFixture):
    """
    A fixture for tests that require a project with multiple
    internal and external packages.
    """

    cpf_root_dir = ''
    cpf_cmake_dir = 'Sources/CPFCMake'
    ci_buildconfigurations_dir = 'Sources/CIBuildConfigurations'
    project = ''

    @classmethod
    def setUpClass(cls, instantiating_test_module=__name__.split('.')[-1]):
        cls.instantiating_module = instantiating_test_module
        cls.project = 'ACPFTestProject'
        cls.cpf_root_dir = testprojectfixture.prepareTestProject('https://github.com/Knitschi/ACPFTestProject.git', cls.project, instantiating_test_module)


    def setUp(self):
        super(ACPFTestProjectFixture, self).setUp(self.project, self.cpf_root_dir, self.cpf_cmake_dir, self.ci_buildconfigurations_dir, self.instantiating_module)        


    #####################################################################################################
    def test_pipeline_works(self):
        """
        Check that the pipeline target builds.
        """
        # Setup
        self.generate_project()

        # Test the pipeline works
        self.build_target('pipeline')


    def test_dlls_are_deployed_into_build_tree(self):
        """
        Check that the deployment of dlls from inlined targets into the build tree works on windows.
        """
        if self.is_windows:
            # Setup
            self.generate_project()

            # Execute
            self.build_target('APackage')

            # Verify that the dlls are in place by running the executable.
            version = self.get_package_version('APackage')
            exe = self.get_package_executable_path_in_build_tree(
                'APackage',
                testprojectfixture.PARENT_CONFIG,
                testprojectfixture.COMPILER_CONFIG,
                version
            )
            self.osa.execute_command_output(str(exe), cwd=str(self.cpf_root_dir), print_output=miscosaccess.OutputMode.ON_ERROR)


    def test_forced_linkage_in_packages_file_works(self):
        """
        This test verifies that STATIC and SHARED keywords override the BUILD_SHARED_LIBS option
        from the configuration.

        The testproject uses the following forced linkage options:

        SHARED EPackage
        STATIC BPackage
        STATIC APackage
        """
        # Setup
        self.generate_project()

        # Test the pipeline works
        self.build_target()

        # Verify

        # shared EPackage
        package = 'EPackage'
        version = self.get_package_version(package)
        binaryOutputDir = self.locations.get_full_path_binary_output_folder(testprojectfixture.PARENT_CONFIG, testprojectfixture.COMPILER_CONFIG)
        dll = binaryOutputDir / self.get_package_shared_lib_path(package, 'LIB', version)
        expectedFiles = [dll]

        # static BPackage
        package = 'BPackage'
        version = self.get_package_version(package)
        binaryOutputDir = self.locations.get_full_path_binary_output_folder(testprojectfixture.PARENT_CONFIG, testprojectfixture.COMPILER_CONFIG)
        lib = binaryOutputDir / self.get_package_static_lib_path(package, 'LIB')
        expectedFiles.append(lib)
        dll = binaryOutputDir / self.get_package_shared_lib_path(package, 'LIB', version)
        unexpectedFiles = [dll]
        
        # static APackage
        package = 'APackage'
        version = self.get_package_version(package)
        binaryOutputDir = self.locations.get_full_path_binary_output_folder(testprojectfixture.PARENT_CONFIG, testprojectfixture.COMPILER_CONFIG)
        lib = binaryOutputDir / self.get_package_static_lib_path(package, 'CONSOLE_APP')
        expectedFiles.append(lib)
        dll = binaryOutputDir / self.get_package_shared_lib_path(package, 'LIB', version)
        unexpectedFiles.append(dll)

        self.assert_files_exist(expectedFiles)
        self.assert_files_do_not_exist(unexpectedFiles)








    
