"""
This module contains automated tests that operate on the SimpleOneLibCPFTestProject project.
"""

import unittest
import os
import pprint
import types
import datetime
import sys
from pathlib import PureWindowsPath, PurePosixPath, PurePath


from Sources.CPFBuildscripts.python import miscosaccess
from . import testprojectfixture
from . import simpleonelibcpftestprojectfixture


############################################################################################
class SimpleOneLibCPFTestProjectFixture5(simpleonelibcpftestprojectfixture.SimpleOneLibCPFTestProjectFixture):
    """
    A fixture for tests that can be done with a minimal project that has no test executable and 
    only a library package.
    """

    cpf_root_dir = ''
    cpf_cmake_dir = 'Sources/external/CPFCMake'
    ci_buildconfigurations_dir = 'Sources/external/CIBuildConfigurations'
    project = ''

    @classmethod
    def setUpClass(cls, instantiating_test_module=__name__.split('.')[-1]):
        cls.instantiating_module = instantiating_test_module
        cls.project = 'SimpleOneLibCPFTestProject'
        cls.cpf_root_dir = testprojectfixture.prepareTestProject('https://github.com/Knitschi/SimpleOneLibCPFTestProject.git', cls.project, cls.cpf_cmake_dir, cls.cpf_buildscripts_dir, cls.instantiating_module)

    def setUp(self):
        super(SimpleOneLibCPFTestProjectFixture5, self).setUp(self.instantiating_module)

    def test_clangtidy_MyLib_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.CLANG_TIDY_MYLIB_TARGET

        # Execute
        self.do_basic_target_tests(target, target, self.is_clang_config())


    def test_valgrind_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.VALGRIND_MYLIB_TARGET

        # Execute
        self.do_basic_target_tests(target, target, self.is_linux_debug_config())


    def test_cotire(self):
        """
        The test only verifies that a cotire generated target is available.
        """
        # Setup
        self.generate_project(['CPF_ENABLE_PRECOMPILED_HEADER=ON', 'COTIRE_MINIMUM_NUMBER_OF_TARGET_SOURCES=1'])
        target = simpleonelibcpftestprojectfixture.COTIRE_TARGET

        # Execute
        self.do_basic_target_tests(target, target, do_uptodate_test=False)


    def test_new_version_is_propagated_to_ConfigVersion_file(self):
        """
        This test was introduced to reproduce bug #31.
        With this bug, the MyLibConfigVersion.cmake file did not contain
        the correct version after an incremental cmake generate step.
        """
        # Setup
        self.generate_project()
        self.build_target(simpleonelibcpftestprojectfixture.PACKAGE_ARCHIVES_MYLIB_TARGET)

        # Execute
        # Make a dummy change
        sourceFile = self.locations.get_full_path_source_folder() / "MyLib/MyLib/function.cpp"
        with open(str(sourceFile), "a") as f:
            f.write("\n")
        # Commit the change
        self.osa.execute_command_output(
            'git commit . -m "Dummy change"',
            cwd=self.cpf_root_dir,
            print_output=miscosaccess.OutputMode.ON_ERROR
        )
        # Do the incremental generate
        self.run_python_command('2_Generate.py')
        # Build the package archive target
        self.build_target(simpleonelibcpftestprojectfixture.PACKAGE_ARCHIVES_MYLIB_TARGET)

        # Verify
        packageVersionFromGit = self.get_package_version("MyLib") # The version from git
        packageVersionVar = 'PACKAGE_VERSION'
        packageVersionConfigFile = self.locations.get_full_path_config_makefile_folder(testprojectfixture.PARENT_CONFIG) / "MyLib/_pckg/dev/MyLib/lib/cmake/MyLib/MyLibConfigVersion.cmake"
        packageVersionFromConfigFile = self.get_cmake_variables_in_file([packageVersionVar], packageVersionConfigFile)[packageVersionVar]

        self.assertEqual(packageVersionFromConfigFile, packageVersionFromGit)


    def test_version_is_written_into_file_info_file(self):
        """
        On Windows we create an .rc file that is used to write version information
        into the generated binaries. This is the information that can be seen when
        right-clicking on a file and opening the "Details" tab.

        This test verifies that this mechanism works.
        """
        # This functionality is only provided by the msvc compiler.
        if not (self.is_visual_studio_config() and self.is_shared_libraries_config()):
            return

        self.generate_project()
        self.build_target(simpleonelibcpftestprojectfixture.MYLIB_TESTS_TARGET)

        # VERIFY
        package = 'MyLib'
        packageType = 'LIB'
        owner = 'Knitschi'
        version = self.get_package_version(package)
        binBaseDir = self.locations.get_full_path_binary_output_folder(testprojectfixture.PARENT_CONFIG, testprojectfixture.COMPILER_CONFIG)
        
        libFile = binBaseDir / self.get_package_shared_lib_path(package, packageType, version)
        shortLibFile = self.get_shared_lib_short_name(package, packageType, version)

        print(libFile)

        # Read the properties from the binary file.
        props = testprojectfixture.get_file_properties(str(libFile))['StringFileInfo']

        # Compare the values
        self.assertEqual(props['CompanyName'], owner)
        self.assertEqual(props['FileDescription'], 'A C++ library used for testing the CPF')
        self.assertEqual(props['FileVersion'], '{0}'.format(version))
        self.assertEqual(props['InternalName'], 'MyLib')
        self.assertEqual(props['LegalCopyright'], 'Copyright {0} {1}'.format(datetime.datetime.now().year, owner) )
        self.assertEqual(props['OriginalFilename'], str(shortLibFile))
        self.assertEqual(props['ProductName'], 'MyLib')
        self.assertEqual(props['ProductVersion'], '{0}'.format(version))
    