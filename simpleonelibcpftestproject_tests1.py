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
class SimpleOneLibCPFTestProjectFixture1(simpleonelibcpftestprojectfixture.SimpleOneLibCPFTestProjectFixture):
    """
    A fixture for tests that can be done with a minimal project that has no test executable and 
    only a library package.
    """

    cpf_root_dir = ''
    project = ''

    @classmethod
    def setUpClass(cls, instantiating_test_module=__name__.split('.')[-1]):
        cls.instantiating_module = instantiating_test_module
        cls.project = 'SimpleOneLibCPFTestProject'
        cls.cpf_root_dir = testprojectfixture.prepareTestProject('https://github.com/Knitschi/SimpleOneLibCPFTestProject.git', cls.project, cls.instantiating_module)

    def setUp(self):
        super(SimpleOneLibCPFTestProjectFixture1, self).setUp(self.project, self.cpf_root_dir, self.instantiating_module)

    def test_configure_script(self):
        """
        This tests the underlying functionality of the '1_Configure.py' script.
        """
        # SETUP
        self.cleanup_generated_files()
        self.run_python_command('Sources/CPFBuildscripts/0_CopyScripts.py')

        # EXECUTE
        # Check that a failed call causes an test exception.
        self.assertRaises(miscosaccess.CalledProcessError, self.run_python_command, '1_Configure.py')

        # Check that configuring an existing variable works.
        # Test overriding existing variables and setting variables with whitespaces.
        self.run_python_command('1_Configure.py MyConfig --inherits {0} -D CPF_ENABLE_RUN_TESTS_TARGET=OFF -D BLUB="bli bla"'.format(testprojectfixture.PARENT_CONFIG))
        self.run_python_command('3_Generate.py MyConfig')
        cmakeCacheVariables = self.osa.execute_command_output(
            'cmake Generated/MyConfig -L',
            cwd=self.cpf_root_dir,
            print_output=miscosaccess.OutputMode.ON_ERROR
            )
        # Note that variables that are added via 1_Configure.py are always of type string
        self.assertIn('CPF_ENABLE_RUN_TESTS_TARGET:STRING=OFF', cmakeCacheVariables)
        self.assertIn('BLUB:STRING=bli bla', cmakeCacheVariables)


    def test_pipeline_target(self):
        """
        Checks that the pipeline target builds and runs all tools.
        """
        # Setup
        self.generate_project(d_options = ['CMAKE_VERBOSE_MAKEFILE=ON']) # we need more output here to verify the binary compile signature.
        target = simpleonelibcpftestprojectfixture.PIPELINE_TARGET

        # Execute
        output = self.build_target(target)

        # Verify
        # Universal tools are run
        self.assert_output_contains_signature(output, target, simpleonelibcpftestprojectfixture.DOXYGEN_TARGET)
        self.assert_output_contains_signature(output, target, simpleonelibcpftestprojectfixture.CLANGTIDY_TARGET)
        self.assert_output_contains_signature(output, target, simpleonelibcpftestprojectfixture.MYLIB_TARGET)
        self.assert_output_contains_signature(output, target, simpleonelibcpftestprojectfixture.MYLIB_TESTS_TARGET)
        self.assert_output_contains_signature(output, target, simpleonelibcpftestprojectfixture.MYLIB_FIXTURES_TARGET)
        self.assert_output_contains_signature(output, target, simpleonelibcpftestprojectfixture.DISTRIBUTION_PACKAGES_MYLIB_TARGET)

        # Config specific tools are run
        if self.is_visual_studio_config() and self.is_debug_compiler_config():
            self.assert_output_contains_signature(output, target, simpleonelibcpftestprojectfixture.OPENCPPCOVERAGE_MYLIB_TARGET)

        if self.is_clang_config():
            self.assert_output_contains_signature(output, target, simpleonelibcpftestprojectfixture.CLANG_TIDY_MYLIB_TARGET)

        if self.is_linux_debug_config():
            self.assert_output_contains_signature(output, target, simpleonelibcpftestprojectfixture.VALGRIND_MYLIB_TARGET)
            # self.assert_output_contains_signature(output, ABI_COMPLIANCE_CHECKER_MYLIB_TARGET)

        else: # The runAllTests target is not included in the pipeline when the valgrind target is available to not run tests twice.
            self.assert_output_contains_signature(output, target, simpleonelibcpftestprojectfixture.RUN_ALL_TESTS_MYLIB_TARGET)


    def test_doxygen_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.DOXYGEN_TARGET
        # More or less every change to a file should trigger doxygen.
        # We restrain ourselves to two files here to save time.
        sources = [
            'Sources/documentation/DoxygenConfig.txt',
            'Sources/MyLib/function.cpp',
        ]
        output = [
            'documentation/tempDoxygenConfig.txt',                                  # test the production of the temp config file works
            'documentation/doxygen/external/CPFDependenciesTransitiveReduced.dot',           # test the dependency dot files are produced.
            'documentation/doxygen/html/index.html'                                          # test the index html file is produced.
        ]

        # Execute
        self.do_basic_target_tests(target, target, source_files=sources, output_files=output)


    def test_distributionPackages_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.DISTRIBUTION_PACKAGES_TARGET

        # Execute
        self.do_basic_target_tests(target, simpleonelibcpftestprojectfixture.DISTRIBUTION_PACKAGES_MYLIB_TARGET)


    def test_runAllTests_target(self):
        # Setup
        self.generate_project()
        target = simpleonelibcpftestprojectfixture.RUN_ALL_TESTS_TARGET

        # Execute
        self.do_basic_target_tests(target, simpleonelibcpftestprojectfixture.RUN_ALL_TESTS_MYLIB_TARGET)


    """ 
        how can we test do this? how can we download previous reports?
        def test_abi_compliance_checker_target_works(self):

        def test__target(self):
            # Setup
            self.generate_project()
            target = ABI_COMPLIANCE_CHECKER_TARGET

            # Execute
            if self.is_linux_debug_config():
            output = self.build_target(target)


        def test__target(self):
            # Setup
            self.generate_project()
            target = ABI_COMPLIANCE_CHECKER_MYLIB_TARGET

            # Execute
            if self.is_linux_debug_config():
            output = self.build_target(target)
    """







       


