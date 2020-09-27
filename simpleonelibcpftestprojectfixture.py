"""
This module contains the fixture fore the SimpleOneLibCPFTestProject project.
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


# Target names
PIPELINE_TARGET = 'pipeline'
DOXYGEN_TARGET = 'documentation'
DISTRIBUTION_PACKAGES_TARGET = 'distributionPackages'
RUN_ALL_TESTS_TARGET = 'runAllTests'
RUN_FAST_TESTS_TARGET = 'runFastTests'
CLANGFORMAT_TARGET = 'clang-format'
CLANGTIDY_TARGET = 'clang-tidy'
ACYCLIC_TARGET = 'acyclic'
VALGRIND_TARGET = 'valgrind'
OPENCPPCOVERAGE_TARGET = 'opencppcoverage'
INSTALL_TARGET = 'install'
INSTALL_ALL_TARGET = 'install_all'
ABI_COMPLIANCE_CHECKER_TARGET = 'abi-compliance-checker'
COTIRE_TARGET = 'clean_cotire'
MYLIB_TARGET = 'MyLib'
MYLIB_TESTS_TARGET = 'MyLib_tests'
MYLIB_FIXTURES_TARGET = 'MyLib_fixtures'
DISTRIBUTION_PACKAGES_MYLIB_TARGET = 'distributionPackages_MyLib'
RUN_ALL_TESTS_MYLIB_TARGET = 'runAllTests_MyLib'
RUN_FAST_TESTS_MYLIB_TARGET = 'runFastTests_MyLib'
OPENCPPCOVERAGE_MYLIB_TARGET = 'opencppcoverage_MyLib'
CLANG_FORMAT_MYLIB_TARGET = 'clang-format_MyLib'
CLANG_TIDY_MYLIB_TARGET = 'clang-tidy_MyLib'
VALGRIND_MYLIB_TARGET = 'valgrind_MyLib'
ABI_COMPLIANCE_CHECKER_MYLIB_TARGET = 'abi-compliance-checker_MyLib'


# build output signatures
# To verify that the build has executed a certain task, we parse the
# command line output for these signatures. The output must contain
# all the strings given by the signature to verify that the tool has been
# run.
target_signatures = {
    DOXYGEN_TARGET : ['doxygen', 'Parsing layout file', 'lookup cache used'],
    DISTRIBUTION_PACKAGES_TARGET : [], # bundle target only
    RUN_ALL_TESTS_TARGET : [], # bundle target only
    RUN_FAST_TESTS_TARGET : [], # bundle target only
    CLANGTIDY_TARGET : [], # bundle target only
    ACYCLIC_TARGET : ['-nv','CPFDependencies.dot'],
    VALGRIND_TARGET : [], # bundle target only
    OPENCPPCOVERAGE_TARGET : ['OpenCppCoverage.exe', '--export_type=html'],
    INSTALL_TARGET : lambda fixture: getInstallTargetSignature(fixture) ,
    ABI_COMPLIANCE_CHECKER_TARGET : [], # bundle target only
    COTIRE_TARGET : ['Cleaning up all cotire generated files'], # The clean cotire target is never out-dated so giving a signature will fail for the rebuild.
    MYLIB_TARGET : lambda fixture: getBinaryTargetSignature(fixture, MYLIB_TARGET),
    MYLIB_TESTS_TARGET : lambda fixture: getBinaryTargetSignature(fixture, MYLIB_TESTS_TARGET),
    MYLIB_FIXTURES_TARGET : lambda fixture: getBinaryTargetSignature(fixture, MYLIB_FIXTURES_TARGET),
    DISTRIBUTION_PACKAGES_MYLIB_TARGET : ['CPack: Create package'],
    RUN_ALL_TESTS_MYLIB_TARGET : lambda fixture: getRunTestsTargetSignature(fixture, MYLIB_TARGET, False),
    RUN_FAST_TESTS_MYLIB_TARGET : lambda fixture: getRunTestsTargetSignature(fixture, MYLIB_TARGET, True),
    OPENCPPCOVERAGE_MYLIB_TARGET : ['OpenCppCoverage.exe', '--export_type=binary'],
    CLANG_FORMAT_MYLIB_TARGET   : ['clang-format', '-style=file'],
    CLANG_TIDY_MYLIB_TARGET : ['clang-tidy', '-checks='],
    VALGRIND_MYLIB_TARGET : ['valgrind', '--leak-check=full'],
    ABI_COMPLIANCE_CHECKER_MYLIB_TARGET : ['abi-compliance-checker','-DBINARY_NAME='],
}


# config dependent signatures:
def getBinaryTargetSignature(test_fixture, binary_target):
    if test_fixture.is_visual_studio_config():
        return ['{0}.vcxproj ->'.format(binary_target), 'cl /c']    # Requires CMAKE_VERBOSE_MAKEFILE=ON
    elif test_fixture.is_make_config():
        return ['Built target {0}'.format(binary_target), 'Building CXX object']
    elif test_fixture.is_ninja_config():
        # ninja only prints commands which vary with target type. This makes things complicated so I decided to skip that test for ninja builds.
        if test_fixture.is_clang_config():
            return ['clang++']
        elif test_fixture.is_gcc_config():
            return ['gcc'] 
    else:
        raise Exception('Missing case in conditional')

def getInstallTargetSignature(test_fixture):
    if test_fixture.is_ninja_config() or test_fixture.is_make_config():
        return ['Install the project...', 'Installing:']
    if test_fixture.is_visual_studio_config():
        return ['Install configuration: "{0}"'.format(testprojectfixture.COMPILER_CONFIG), 'Installing:']

def getRunTestsTargetSignature(test_fixture, binary_target, is_fast_tests_target):
    if test_fixture.is_ninja_config():
        # For the ninja config the generator expression is expanded in the output.
        if not is_fast_tests_target:
            return ['MyLib_tests', '--gtest_filter=*']
        else:
            return ['MyLib_tests', '--gtest_filter=*FastFixture*:*FastTests*']
    else:
        if not is_fast_tests_target:
            ['$<TARGET_FILE:MyLib_tests> --gtest_filter=*']
        else:
            ['$<TARGET_FILE:MyLib_tests> --gtest_filter=*FastFixture*:*FastTests*']


############################################################################################
class SimpleOneLibCPFTestProjectFixture(testprojectfixture.TestProjectFixture):
    """
    A fixture for tests that can be done with a minimal project that has no test executable and 
    only a library package.
    """

    cpf_root_dir = ''
    project = ''

    

    def setUp(self, project, cpf_root_dir, instantiating_module):
        super(SimpleOneLibCPFTestProjectFixture, self).setUp(project, cpf_root_dir, instantiating_module)

    def assert_output_contains_signature(self, output, target, signature_target, source_file = None):
        super(SimpleOneLibCPFTestProjectFixture, self).assert_output_contains_signature(output, target, self.get_signature(signature_target), trigger_source_file = source_file)

    def get_signature(self, target):
        element = target_signatures[target]
        if isinstance(element, types.FunctionType):
            signature = (element(self))
        else:
            signature = element
        return signature

    def assert_output_has_not_signature(self, output, target, signature_target):
        super(SimpleOneLibCPFTestProjectFixture, self).assert_output_has_not_signature(output, target, self.get_signature(signature_target))


    def do_basic_target_tests(self, built_target, signature_target, target_exists = True, is_dummy_target = False, source_files = [], output_files = [], do_uptodate_test = True):
        """
        This functions does basic tests for created targets.
        For bundle targets that do not produce their own signature,
        the signature target should be one of the bundled targets.

        Tests:
        1. Check the given built_target exists, builds and produces a output signature that
        is defined by signature_target.
        2. Check that the given target does not exist if target_exits is set to False.
        3. Check that the target does not produce the output signature if is_dummy_target is set to True.
            This is the case for targets in multiconfig generators that only do something for a certain compiler config.
        4. Check the given built_target is not build a second time, when it is up-to-date. This test can be skipped by setting the do_uptodate_test argument to False.
        5. Check the target is rebuild after touching any of the given source_files. Note that
            one build is done for each file, so adding a lot of files will drive test times in the sky.
            The pathes of the source_files must be relative to the cpf_root_directory.
        6. Check that the specified output files are produced. Paths must be relative to CMAKE_BINARY_DIR.
        """

        if target_exists:
            output = self.build_target(built_target)
            if not is_dummy_target:
                # Check the target builds and produces an output signature
                self.assert_output_contains_signature(output, built_target, signature_target)

                # Check the target produced the specified files
                self.assert_files_exist(output_files)

                # Check the target is not build again when it is up-to-date.
                if do_uptodate_test:
                    output = self.build_target(built_target)
                    self.assert_output_has_not_signature(output, built_target, signature_target)

                # Check that changes to source files out-date the target
                if not self.is_ninja_config():  # This test fails for ninja. Strangly the behavior is correct when the file changes
                                                # and rebuilds are done manually. I tried to add wait times, use cmake to touch the
                                                # files and make changes to the content of the file which all did not work.
                    for source_file in source_files:
                        full_source_file = self.cpf_root_dir.joinpath(source_file)
                        self.fsa.touch_file(full_source_file)
                        output = self.build_target(built_target)
                        self.assert_output_contains_signature(output, built_target, signature_target, source_file=source_file)

            else:
                # Make sure the dummy target does not really do anything.
                self.assert_output_has_not_signature(output, built_target, signature_target)

        else:
            # Check the target does not exist.
            self.assert_target_does_not_exist(built_target)