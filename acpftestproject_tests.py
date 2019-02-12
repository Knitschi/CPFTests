"""
This module contains automated tests that operate on the ACPFTestProject project.
"""

import unittest
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
    project = ''

    @classmethod
    def setUpClass(cls):
        cls.project = 'ACPFTestProject'
        cls.cpf_root_dir = testprojectfixture.prepareTestProject('https://github.com/Knitschi/ACPFTestProject.git', cls.project)


    def setUp(self):
        super(ACPFTestProjectFixture, self).setUp(self.project, self.cpf_root_dir)        


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
        package = 'EPackage'
        versionE = self.get_package_version(package)
        binaryOutputDir = self.locations.get_full_path_binary_output_folder(package, testprojectfixture.PARENT_CONFIG, testprojectfixture.COMPILER_CONFIG)
        eDll = binaryOutputDir / self.get_package_shared_lib_path(package, 'LIB', versionE)
        files = [eDll]

        package = 'BPackage'
        binaryOutputDir = self.locations.get_full_path_binary_output_folder(package, testprojectfixture.PARENT_CONFIG, testprojectfixture.COMPILER_CONFIG)
        bDll = binaryOutputDir / self.get_package_static_lib_path(package, 'LIB')
        files.append(bDll)

        package = 'APackage'
        binaryOutputDir = self.locations.get_full_path_binary_output_folder(package, testprojectfixture.PARENT_CONFIG, testprojectfixture.COMPILER_CONFIG)
        bDll = binaryOutputDir / self.get_package_static_lib_path(package, 'CONSOLE_APP')
        files.append(bDll)

        self.assert_files_exist(files)








    
