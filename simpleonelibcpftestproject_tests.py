"""
This module contains automated tests that operate on the SimpleOneLibCPFTestProject project.
"""

import unittest
import os
import pprint
import types

from Sources.CPFBuildscripts.python import miscosaccess

from . import testprojectfixture


# Target names
PIPELINE_TARGET = 'pipeline'
DOXYGEN_TARGET = 'doxygen'
DISTRIBUTION_PACKAGES_TARGET = 'distributionPackages'
RUN_ALL_TESTS_TARGET = 'runAllTests'
RUN_FAST_TESTS_TARGET = 'runFastTests'
STATIC_ANALYSIS_TARGET = 'staticAnalysis'
DYNAMIC_ANALYSIS_TARGET = 'dynamicAnalysis'
INSTALL_TARGET = 'install'
ABI_COMPLIANCE_CHECKER_TARGET = 'abi-compliance-checker'

MYLIB_TARGET = 'MyLib'
MYLIB_TESTS_TARGET = 'MyLib_tests'
MYLIB_FIXTURES_TARGET = 'MyLib_fixtures'
DISTRIBUTION_PACKAGES_MYLIB_TARGET = 'distributionPackages_MyLib'
INSTALL_MYLIB_TARGET = 'install_MyLib'
RUN_ALL_TESTS_MYLIB_TARGET = 'runAllTests_MyLib'
RUN_FAST_TESTS_MYLIB_TARGET = 'runFastTests_MyLib'
OPENCPPCOVERAGE_MYLIB_TARGET = 'opencppcoverage_MyLib'
CLANG_TIDY_MYLIB_TARGET = 'clang-tidy_MyLib'
VALGRIND_MYLIB_TARGET = 'valgrind_MyLib'
ABI_COMPLIANCE_CHECKER_MYLIB_TARGET = 'abi-compliance-checker_MyLib'


# build output signatures
# To verify that the build has executed a certain task, we parse the
# command line output for these signatures. The output must contain
# all the strings given by the signature to verify that the tool has been
# run.
target_signatures = {
    DOXYGEN_TARGET : ['doxygen', 'doxyindexer', 'tred','lookup cache used'],
    DISTRIBUTION_PACKAGES_TARGET : [], # bundle target only
    RUN_ALL_TESTS_TARGET : [], # bundle target only
    RUN_FAST_TESTS_TARGET : [], # bundle target only
    STATIC_ANALYSIS_TARGET : ['acyclic'],
    DYNAMIC_ANALYSIS_TARGET : [], # bundle target only
    INSTALL_TARGET : [], # bundle target only
    ABI_COMPLIANCE_CHECKER_TARGET : [], # bundle target only
    MYLIB_TARGET : lambda fixture: getBinaryTargetSignature(fixture, MYLIB_TARGET),
    MYLIB_TESTS_TARGET : lambda fixture: getBinaryTargetSignature(fixture, MYLIB_TESTS_TARGET),
    MYLIB_FIXTURES_TARGET : lambda fixture: getBinaryTargetSignature(fixture, MYLIB_FIXTURES_TARGET),
    DISTRIBUTION_PACKAGES_MYLIB_TARGET : ['CPack: Create package'],
    INSTALL_MYLIB_TARGET : ['-- Installing: '],
    RUN_ALL_TESTS_MYLIB_TARGET : ['$<TARGET_FILE:MyLib_tests> -TestFilesDir', '--gtest_filter=*'],
    RUN_FAST_TESTS_MYLIB_TARGET : ['$<TARGET_FILE:MyLib_tests> -TestFilesDir', '--gtest_filter=*FastFixture*:*FastTests*'],
    OPENCPPCOVERAGE_MYLIB_TARGET : ['OpenCppCoverage.exe" --export_type=binary'],
    CLANG_TIDY_MYLIB_TARGET : ['clang-tidy', '-checks='],
    VALGRIND_MYLIB_TARGET : ['valgrind', '--leak-check=full'],
    ABI_COMPLIANCE_CHECKER_MYLIB_TARGET : ['abi-compliance-checker','-DBINARY_NAME='],
}


# config dependent signatures:
def getBinaryTargetSignature(test_fixture, binary_target):
    if test_fixture.is_visual_studio_config():
        return ['{0}.vcxproj'.format(binary_target)]
    elif test_fixture.is_make_config():
        return ['Built target {0}'.format(binary_target)]
    elif test_fixture.is_ninja_config():
        return [''] # ninja only prints commands which vary with target type. This makes things complicated so I decided to skip that test for ninja builds.
    else:
        raise Exception('Missing case in conditional')




############################################################################################
class SimpleOneLibCPFTestProjectFixture(testprojectfixture.TestProjectFixture):
    """
    A fixture for tests that can be done with a minimal project that has no test executable and 
    only a library package.
    """

    cpf_root_dir = ''
    project = ''

    @classmethod
    def setUpClass(cls):
        cls.project = 'SimpleOneLibCPFTestProject'
        cls.cpf_root_dir = testprojectfixture.prepareTestProject('https://github.com/Knitschi/SimpleOneLibCPFTestProject.git', cls.project)

    def setUp(self):
        super(SimpleOneLibCPFTestProjectFixture, self).setUp(self.project, self.cpf_root_dir)

    def assert_output_contains_signature(self, output, target):
        super(SimpleOneLibCPFTestProjectFixture, self).assert_output_contains_signature(output, target, self.get_signature(target))

    def get_signature(self, target):
        element = target_signatures[target]
        if isinstance(element, types.FunctionType):
            signature = (element(self))
        else:
            signature = element
        return signature

    def assert_output_has_not_signature(self, output, target):
        super(SimpleOneLibCPFTestProjectFixture, self).assert_output_has_not_signature(output, target, self.get_signature(target))

    def test_configure_script(self):
        """
        This tests the underlying functionality of the '1_Configure.py' script.
        """
        # SETUP
        self.cleanup_generated_files()
        self.run_python_command('Sources/CPFBuildscripts/0_CopyScripts.py')

        # EXECUTE
        # Check that a failed call causes an test exception.
        self.assertRaises(miscosaccess.CalledProcessError, self.run_python_command, '1_Configure.py {0}'.format(testprojectfixture.PARENT_CONFIG))

        # Check that configuring an existing variable works.
        # Test overriding existing variables and setting variables with whitespaces.
        self.run_python_command('1_Configure.py MyConfig --inherits {0} -D CPF_ENABLE_DOXYGEN_TARGET=OFF -D BLUB="bli bla"'.format(testprojectfixture.PARENT_CONFIG))
        self.run_python_command('2_Generate.py MyConfig')
        cmakeCacheVariables = self.osa.execute_command_output('cmake Generated/MyConfig -L', cwd=self.cpf_root_dir, print_output=False, print_command=False)
        # Note that variables that are added via 1_Configure.py are always of type string
        self.assertIn('CPF_ENABLE_DOXYGEN_TARGET:STRING=OFF', cmakeCacheVariables)
        self.assertIn('BLUB:STRING=bli bla', cmakeCacheVariables)


    def test_pipeline_target(self):
        """
        Checks that the pipeline target builds and runs all tools.
        """
        # Setup
        self.generate_project()

        # Execute
        output = self.build_target(PIPELINE_TARGET)

        # Verify
        # Universal tools are run
        self.assert_output_contains_signature(output, DOXYGEN_TARGET)
        self.assert_output_contains_signature(output, STATIC_ANALYSIS_TARGET)
        self.assert_output_contains_signature(output, MYLIB_TARGET)
        self.assert_output_contains_signature(output, MYLIB_TESTS_TARGET)
        self.assert_output_contains_signature(output, MYLIB_FIXTURES_TARGET)
        self.assert_output_contains_signature(output, DISTRIBUTION_PACKAGES_MYLIB_TARGET)
        self.assert_output_contains_signature(output, INSTALL_MYLIB_TARGET)

        # Config specific tools are run
        if self.is_visual_studio_config() and self.is_debug_compiler_config():
            self.assert_output_contains_signature(output, OPENCPPCOVERAGE_MYLIB_TARGET)

        if self.is_clang_config():
            self.assert_output_contains_signature(output, CLANG_TIDY_MYLIB_TARGET)

        if self.is_linux_debug_config():
            self.assert_output_contains_signature(output, VALGRIND_MYLIB_TARGET)
            # self.assert_output_contains_signature(output, ABI_COMPLIANCE_CHECKER_MYLIB_TARGET)

        else: # The runAllTests target is not included in the pipeline when the valgrind target is available to not run tests twice.
            self.assert_output_contains_signature(output, RUN_ALL_TESTS_MYLIB_TARGET)


    def test_doxygen_target(self):
        # Setup
        self.generate_project()
        target = DOXYGEN_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, target)


    def test_distributionPackages_target(self):
        # Setup
        self.generate_project()
        target = DISTRIBUTION_PACKAGES_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, DISTRIBUTION_PACKAGES_MYLIB_TARGET)


    def test_runAllTests_target(self):
        # Setup
        self.generate_project()
        target = RUN_ALL_TESTS_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, RUN_ALL_TESTS_MYLIB_TARGET)


    def test_runFastTests_target(self):
        # Setup
        self.generate_project()
        target = RUN_FAST_TESTS_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, RUN_FAST_TESTS_MYLIB_TARGET)


    def test_staticAnalysis_target(self):
        # Setup
        self.generate_project()
        target = STATIC_ANALYSIS_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, STATIC_ANALYSIS_TARGET)
        if self.is_clang_config():
            self.assert_output_contains_signature(output, CLANG_TIDY_MYLIB_TARGET)


    def test_dynamicAnalysis_target(self):
        # Setup
        self.generate_project()
        target = DYNAMIC_ANALYSIS_TARGET

        # Execute
        if self.is_msvc_or_debug_config():
            output = self.build_target(target)
            if self.is_visual_studio_config():
                self.assert_output_contains_signature(output, OPENCPPCOVERAGE_MYLIB_TARGET)
            if self.is_linux_debug_config():
                self.assert_output_contains_signature(output, VALGRIND_MYLIB_TARGET)
        else:
            self.assert_target_does_not_exist(target)


    def test_install_target(self):
        # Setup
        self.generate_project()
        target = INSTALL_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, INSTALL_MYLIB_TARGET)


    def test_MyLib_target(self):
        # Setup
        self.generate_project()
        target = MYLIB_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, target)


    def test_MyLib_Tests_target(self):
        # Setup
        self.generate_project()
        target = MYLIB_TESTS_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, target)


    def test_MyLib_Fixtures_target(self):
        # Setup
        self.generate_project()
        target = MYLIB_FIXTURES_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, target)


    def test_distributionPackages_MyLib_target(self):
        # Setup
        self.generate_project()
        target = DISTRIBUTION_PACKAGES_MYLIB_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, target)


    def test_install_MyLib_target(self):
        # Setup
        self.generate_project()
        target = INSTALL_MYLIB_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, target)


    def test_runAllTests_MyLib_target(self):
        # Setup
        self.generate_project()
        target = RUN_ALL_TESTS_MYLIB_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, target)


    def test_runFastTests_MyLib_target(self):
        # Setup
        self.generate_project()
        target = RUN_FAST_TESTS_MYLIB_TARGET

        # Execute
        output = self.build_target(target)
        self.assert_output_contains_signature(output, target)


    def test_opencppcoverage_target(self):
        """
        Check that the target runs the OpenCppCoverage.exe for the
        compiler debug config and not for the release config.
        """
        # Setup
        self.generate_project()
        target = OPENCPPCOVERAGE_MYLIB_TARGET

        # Execute
        if self.is_visual_studio_config():
            output = self.build_target(target)
            if self.is_debug_compiler_config():
                # check that the tool is run for the debug configuration.
                self.assert_output_contains_signature(output, target)
            else:
                # check that the tool is not run for the release configuration.
                self.assert_output_has_not_signature(output, target)
        else:
            self.assert_target_does_not_exist(target)


    def test_clangtidy_MyLib_target(self):
        # Setup
        self.generate_project()
        target = CLANG_TIDY_MYLIB_TARGET

        # Execute
        if self.is_clang_config():
            output = self.build_target(target)
            self.assert_output_contains_signature(output, target)
        else:
            self.assert_target_does_not_exist(target)


    def test_valgrind_target(self):
        # Setup
        self.generate_project()
        target = VALGRIND_MYLIB_TARGET

        # Execute
        if self.is_linux_debug_config():
            output = self.build_target(target)
            self.assert_output_contains_signature(output, target)
        else:
            self.assert_target_does_not_exist(target)


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
       


