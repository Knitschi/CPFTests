"""
This module contains automated tests that operate on the SimpleOneLibCPFTestProject project.
"""

import unittest
import os
import pprint
import types
import datetime
from pathlib import PureWindowsPath, PurePosixPath, PurePath


from Sources.CPFBuildscripts.python import miscosaccess
from . import testprojectfixture


# Target names
PIPELINE_TARGET = 'pipeline'
DOXYGEN_TARGET = 'documentation'
DISTRIBUTION_PACKAGES_TARGET = 'distributionPackages'
RUN_ALL_TESTS_TARGET = 'runAllTests'
RUN_FAST_TESTS_TARGET = 'runFastTests'
CLANGTIDY_TARGET = 'clang-tidy'
ACYCLIC_TARGET = 'acyclic'
VALGRIND_TARGET = 'valgrind'
OPENCPPCOVERAGE_TARGET = 'opencppcoverage'
INSTALL_TARGET = 'install'
ABI_COMPLIANCE_CHECKER_TARGET = 'abi-compliance-checker'
COTIRE_TARGET = 'clean_cotire'
MYLIB_TARGET = 'MyLib'
MYLIB_TESTS_TARGET = 'MyLib_tests'
MYLIB_FIXTURES_TARGET = 'MyLib_fixtures'
DISTRIBUTION_PACKAGES_MYLIB_TARGET = 'distributionPackages_MyLib'
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
    RUN_ALL_TESTS_MYLIB_TARGET : ['$<TARGET_FILE:MyLib_tests> -TestFilesDir', '--gtest_filter=*'],
    RUN_FAST_TESTS_MYLIB_TARGET : ['$<TARGET_FILE:MyLib_tests> -TestFilesDir', '--gtest_filter=*FastFixture*:*FastTests*'],
    OPENCPPCOVERAGE_MYLIB_TARGET : ['OpenCppCoverage.exe', '--export_type=binary'],
    CLANG_TIDY_MYLIB_TARGET : ['clang-tidy', '-checks='],
    VALGRIND_MYLIB_TARGET : ['valgrind', '--leak-check=full'],
    ABI_COMPLIANCE_CHECKER_MYLIB_TARGET : ['abi-compliance-checker','-DBINARY_NAME='],
}


# config dependent signatures:
def getBinaryTargetSignature(test_fixture, binary_target):
    if test_fixture.is_visual_studio_config():
        return ['{0}.vcxproj'.format(binary_target), 'CL.exe']
    elif test_fixture.is_make_config():
        return ['Built target {0}'.format(binary_target), 'Building CXX object']
    elif test_fixture.is_ninja_config():
        return ['MyLib', 'Building CXX object'] # ninja only prints commands which vary with target type. This makes things complicated so I decided to skip that test for ninja builds.
    else:
        raise Exception('Missing case in conditional')

def getInstallTargetSignature(test_fixture):
    if test_fixture.is_ninja_config() or test_fixture.is_make_config():
        return ['Install the project...', 'Installing:']
    if test_fixture.is_visual_studio_config():
        return ['Install configuration: "{0}"'.format(testprojectfixture.COMPILER_CONFIG), 'Installing:']


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
        self.run_python_command('2_Generate.py MyConfig')
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
        self.generate_project()
        target = PIPELINE_TARGET

        # Execute
        output = self.build_target(target)

        # Verify
        # Universal tools are run
        self.assert_output_contains_signature(output, target, DOXYGEN_TARGET)
        self.assert_output_contains_signature(output, target, CLANGTIDY_TARGET)
        self.assert_output_contains_signature(output, target, MYLIB_TARGET)
        self.assert_output_contains_signature(output, target, MYLIB_TESTS_TARGET)
        self.assert_output_contains_signature(output, target, MYLIB_FIXTURES_TARGET)
        self.assert_output_contains_signature(output, target, DISTRIBUTION_PACKAGES_MYLIB_TARGET)

        # Config specific tools are run
        if self.is_visual_studio_config() and self.is_debug_compiler_config():
            self.assert_output_contains_signature(output, target, OPENCPPCOVERAGE_MYLIB_TARGET)

        if self.is_clang_config():
            self.assert_output_contains_signature(output, target, CLANG_TIDY_MYLIB_TARGET)

        if self.is_linux_debug_config():
            self.assert_output_contains_signature(output, target, VALGRIND_MYLIB_TARGET)
            # self.assert_output_contains_signature(output, ABI_COMPLIANCE_CHECKER_MYLIB_TARGET)

        else: # The runAllTests target is not included in the pipeline when the valgrind target is available to not run tests twice.
            self.assert_output_contains_signature(output, target, RUN_ALL_TESTS_MYLIB_TARGET)


    def test_doxygen_target(self):
        # Setup
        self.generate_project()
        target = DOXYGEN_TARGET
        # More or less every change to a file should trigger doxygen.
        # We restrain ourselves to two files here to save time.
        sources = [
            'Sources/documentation/DoxygenConfig.txt',
            'Sources/MyLib/function.cpp',
        ]
        output = [
            '_CPF/documentation/tempDoxygenConfig.txt',                             # test the production of the temp config file works
            'html/doxygen/external/CPFDependenciesTransitiveReduced.dot',           # test the dependency dot files are produced.
            'html/doxygen/html/index.html'                                          # test the index html file is produced.
        ]

        # Execute
        self.do_basic_target_tests(target, target, source_files=sources, output_files=output)


    def test_distributionPackages_target(self):
        # Setup
        self.generate_project()
        target = DISTRIBUTION_PACKAGES_TARGET

        # Execute
        self.do_basic_target_tests(target, DISTRIBUTION_PACKAGES_MYLIB_TARGET)


    def test_runAllTests_target(self):
        # Setup
        self.generate_project()
        target = RUN_ALL_TESTS_TARGET

        # Execute
        self.do_basic_target_tests(target, RUN_ALL_TESTS_MYLIB_TARGET)


    def test_runFastTests_target(self):
        # Setup
        self.generate_project()
        target = RUN_FAST_TESTS_TARGET

        # Execute
        self.do_basic_target_tests(target, RUN_FAST_TESTS_MYLIB_TARGET)


    def test_clangtidy_target(self):
        # Setup
        self.generate_project()
        target = CLANGTIDY_TARGET

        # Execute
        # Check the target builds
        self.do_basic_target_tests(target, CLANG_TIDY_MYLIB_TARGET, target_exists=self.is_clang_config())


    def test_acylic_target(self):
        # Setup
        self.generate_project()
        target = ACYCLIC_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_valgrind_target(self):
        # Setup
        self.generate_project()
        target = VALGRIND_TARGET
        sources = [
            'Sources/MyLib/function.cpp',
        ]

        # Execute
        self.do_basic_target_tests( 
            target, 
            VALGRIND_MYLIB_TARGET, 
            target_exists=self.is_linux_debug_config(),
            source_files=sources
        )


    def test_opencppcoverage_target(self):
        # Setup
        self.generate_project()
        target = OPENCPPCOVERAGE_TARGET
        sources = [
            'Sources/MyLib/function.cpp',
        ]
        
        output = [
            'html/OpenCppCoverage/index.html',
        ]

        # Execute
        self.do_basic_target_tests( 
            target, 
            target, 
            target_exists=self.is_visual_studio_config(),
            is_dummy_target=testprojectfixture.COMPILER_CONFIG.lower() != 'Debug',
            source_files=sources,
            output_files=output
        )


    def test_install_target(self):
        # Setup
        self.generate_project(d_options=['CMAKE_INSTALL_PREFIX="{0}"'.format(self.cpf_root_dir / 'install_tree')])
        target = INSTALL_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_MyLib_target(self):
        # Setup
        self.generate_project()
        target = MYLIB_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_MyLib_Tests_target(self):
        # Setup
        self.generate_project()
        target = MYLIB_TESTS_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_MyLib_Fixtures_target(self):
        # Setup
        self.generate_project()
        target = MYLIB_FIXTURES_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_distributionPackages_MyLib_target(self):
        """
        Not that this test only tests if the package is created
        and if it is properly rebuild. The correctness of the 
        the package content is tested in acpftestproject_tests.
        """
        # Setup
        self.generate_project()
        target = DISTRIBUTION_PACKAGES_MYLIB_TARGET

        sources = [
            'Sources/MyLib/function.cpp'
        ]

        # Check the zip file is created.
        distPackagePath = self.get_full_distribution_package_path('MyLib', '7Z', 'CT_DEVELOPER')
        output = [
            distPackagePath
        ]

        # Execute
        self.do_basic_target_tests(target, target, source_files=sources, output_files=output)

    def test_runAllTests_MyLib_target(self):
        # Setup
        self.generate_project()
        target = RUN_ALL_TESTS_MYLIB_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_runFastTests_MyLib_target(self):
        # Setup
        self.generate_project()
        target = RUN_FAST_TESTS_MYLIB_TARGET

        # Execute
        self.do_basic_target_tests(target, target)


    def test_opencppcoverage_target(self):
        """
        Check that the target runs the OpenCppCoverage.exe for the
        compiler debug config and not for the release config.
        """
        # Setup
        self.generate_project()
        target = OPENCPPCOVERAGE_MYLIB_TARGET
        sources = [
            'Sources/MyLib/function.cpp'
        ]
        output = []
        if self.is_visual_studio_config() and self.is_debug_compiler_config():
            output.extend([
                '_CPF/opencppcoverage_MyLib/MyLib_tests.cov'
            ])

        # Execute
        self.do_basic_target_tests(
            target, 
            target, 
            self.is_visual_studio_config(), 
            not self.is_debug_compiler_config(),
            source_files=sources,
            output_files=output
        )


    def test_clangtidy_MyLib_target(self):
        # Setup
        self.generate_project()
        target = CLANG_TIDY_MYLIB_TARGET

        # Execute
        self.do_basic_target_tests(target, target, self.is_clang_config())


    def test_valgrind_target(self):
        # Setup
        self.generate_project()
        target = VALGRIND_MYLIB_TARGET

        # Execute
        self.do_basic_target_tests(target, target, self.is_linux_debug_config())


    def test_cotire(self):
        """
        The test only verifies that a cotire generated target is available.
        """
        # Setup
        self.generate_project(['CPF_ENABLE_PRECOMPILED_HEADER=ON', 'COTIRE_MINIMUM_NUMBER_OF_TARGET_SOURCES=1'])
        target = COTIRE_TARGET

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
        self.build_target(DISTRIBUTION_PACKAGES_MYLIB_TARGET)

        # Execute
        # Make a dummy change
        sourceFile = self.locations.get_full_path_source_folder() / "MyLib/function.cpp"
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
        # Build the distribution package target
        self.build_target(DISTRIBUTION_PACKAGES_MYLIB_TARGET)

        # Verify
        packageVersionFromGit = self.get_package_version("MyLib") # The version from git
        packageVersionVar = 'PACKAGE_VERSION'
        packageVersionConfigFile = self.locations.get_full_path_config_makefile_folder(testprojectfixture.PARENT_CONFIG) / "_pckg/{0}/dev/MyLib/MyLib/lib/cmake/MyLib/MyLibConfigVersion.cmake".format(testprojectfixture.COMPILER_CONFIG)
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
        self.build_target(MYLIB_TESTS_TARGET)

        # VERIFY
        package = 'MyLib'
        packageType = 'LIB'
        owner = 'Dummy Owner'
        version = self.get_package_version(package)
        binBaseDir = self.locations.get_full_path_binary_output_folder(package, testprojectfixture.PARENT_CONFIG, testprojectfixture.COMPILER_CONFIG)
        
        libFile = binBaseDir / self.get_package_shared_lib_path(package, packageType, version)
        shortLibFile = self.get_shared_lib_short_name(package, packageType, version)

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







       


