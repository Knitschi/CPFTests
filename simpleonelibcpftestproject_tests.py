"""
This module contains automated tests that operate on the SimpleOneLibCPFTestProject project.
"""

import unittest
import os
import pprint
import types
from pathlib import PureWindowsPath, PurePosixPath, PurePath

from Sources.CPFBuildscripts.python import miscosaccess

from . import testprojectfixture


# Target names
PIPELINE_TARGET = 'pipeline'
DOXYGEN_TARGET = 'doxygen'
DISTRIBUTION_PACKAGES_TARGET = 'distributionPackages'
RUN_ALL_TESTS_TARGET = 'runAllTests'
RUN_FAST_TESTS_TARGET = 'runFastTests'
CLANGTIDY_TARGET = 'clang-tidy'
ACYCLIC_TARGET = 'acyclic'
VALGRIND_TARGET = 'valgrind'
OPENCPPCOVERAGE_TARGET = 'opencppcoverage'
INSTALL_TARGET = 'install'
ABI_COMPLIANCE_CHECKER_TARGET = 'abi-compliance-checker'

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
    INSTALL_TARGET : ['Install the project...', 'Installing:'],
    ABI_COMPLIANCE_CHECKER_TARGET : [], # bundle target only
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


    def do_basic_target_tests(self, built_target, signature_target, target_exists = True, is_dummy_target = False, source_files = [], output_files = []):
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
        4. Check the given built_target is not build a second time, when it is up-to-date.
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
        self.assertRaises(miscosaccess.CalledProcessError, self.run_python_command, '1_Configure.py {0}'.format(testprojectfixture.PARENT_CONFIG))

        # Check that configuring an existing variable works.
        # Test overriding existing variables and setting variables with whitespaces.
        self.run_python_command('1_Configure.py MyConfig --inherits {0} -D CPF_ENABLE_DOXYGEN_TARGET=OFF -D BLUB="bli bla"'.format(testprojectfixture.PARENT_CONFIG))
        self.run_python_command('2_Generate.py MyConfig')
        cmakeCacheVariables = self.osa.execute_command_output(
            'cmake Generated/MyConfig -L',
            cwd=self.cpf_root_dir,
            print_output=miscosaccess.OutputMode.ON_ERROR
            )
        # Note that variables that are added via 1_Configure.py are always of type string
        self.assertIn('CPF_ENABLE_DOXYGEN_TARGET:STRING=OFF', cmakeCacheVariables)
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
            '_CPF/doxygen/tempDoxygenConfig.txt',                           # test the production of the temp config file works
            'html/doxygen/external/CPFDependenciesTransitiveReduced.dot',   # test the dependency dot files are produced.
            'html/doxygen/index.html'                                       # test the entry file is produced.
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


    def get_expected_package_content(self, prefix_dir, version):

        packageFiles = []
        symlinks = []

        config = testprojectfixture.COMPILER_CONFIG.lower()

        # location primitives
        prefix_dir = PurePosixPath(prefix_dir)
        sharedLibOutputDir = ''
        if self.is_windows():
            sharedLibOutputDir = prefix_dir
        else:
            sharedLibOutputDir = prefix_dir / 'lib'

        runtimeOutputDir = ''
        if self.is_windows():
            runtimeOutputDir = prefix_dir
        else:
            runtimeOutputDir = prefix_dir / 'bin'

        staticLibOutputDir = prefix_dir / 'lib'
        
        libBaseName = self.get_target_binary_base_name('MyLib', testprojectfixture.COMPILER_CONFIG)
        testExeBaseName = self.get_target_binary_base_name('MyLib_tests', testprojectfixture.COMPILER_CONFIG)
        fixtureLibBaseName = self.get_target_binary_base_name('MyLib_fixtures', testprojectfixture.COMPILER_CONFIG)
        
        exeVersionPostfix = ''
        if self.is_linux():
            exeVersionPostfix += '-' + version

        sharedLibExtension = self.get_shared_lib_extension()
        staticLibExtension = self.get_static_lib_extension()
        exeExtension = self.get_exe_extension()
        versionExtension = '.' + version


        # Assemble pathes for package files.

        # CMake package files
        cmakeFilesPath = staticLibOutputDir / 'cmake/MyLib'
        packageFiles.extend([
            cmakeFilesPath / 'MyLibConfig.cmake',
            cmakeFilesPath / 'MyLibConfigVersion.cmake',
            cmakeFilesPath / 'MyLibTargets-{0}.cmake'.format(config),
            cmakeFilesPath / 'MyLibTargets.cmake',
        ])

        # Public header files
        includePath = prefix_dir / 'include/MyLib'
        packageFiles.extend([
            includePath / 'function.h',
            includePath / 'fixture.h',
            includePath / 'mylib_export.h',
            includePath / 'mylib_tests_export.h',
            includePath / 'cpfPackageVersion_MyLib.h'
        ])

        # Library files
        if self.is_shared_libraries_config():
            packageFiles.extend([
                sharedLibOutputDir / (libBaseName + sharedLibExtension + versionExtension),
                sharedLibOutputDir / (fixtureLibBaseName + sharedLibExtension + versionExtension)
            ])
        else:
            packageFiles.extend([
                staticLibOutputDir / (libBaseName + staticLibExtension ),
                staticLibOutputDir / (fixtureLibBaseName + staticLibExtension )
            ])

        # Test executable
        packageFiles.extend([
            runtimeOutputDir / (testExeBaseName + exeVersionPostfix + exeExtension),
        ])

        # Platform dependend files
        if self.is_windows():

            # On windows .lib files are also created for shared libraris.
            if self.is_shared_libraries_config():
                packageFiles.extend([
                    staticLibOutputDir / (libBaseName + staticLibExtension),
                    staticLibOutputDir / (fixtureLibBaseName  + staticLibExtension)
                ])

            # pdb and source files
            if self.is_debug_compiler_config():

                if self.is_shared_libraries_config():
                    packageFiles.extend([
                        sharedLibOutputDir / '{0}.pdb'.format(libBaseName),
                        sharedLibOutputDir / '{0}.pdb'.format(fixtureLibBaseName)
                    ])

                packageFiles.extend([
                    staticLibOutputDir / '{0}-compiler.pdb'.format(libBaseName),
                    staticLibOutputDir / '{0}-compiler.pdb'.format(fixtureLibBaseName),
                    staticLibOutputDir / '{0}-compiler.pdb'.format(testExeBaseName)
                ])

                # Source files are required for debugging with pdb files.
                sourcePath = prefix_dir / 'src/MyLib'
                packageFiles.extend([
                    sourcePath / 'cpfPackageVersion_MyLib.h',
                    sourcePath / 'fixture.cpp',
                    sourcePath / 'fixture.h',
                    sourcePath / 'function.cpp',
                    sourcePath / 'function.h',
                    sourcePath / 'mylib_export.h',
                    sourcePath / 'mylib_tests_export.h'
                ])

        if self.is_linux():

            # Abi dumps
            otherPath = prefix_dir / 'other'
            if self.is_debug_compiler_config():
                packageFiles.extend([
                    otherPath / 'ABI_{0}.{1}.dump'.format(libBaseName, version),
                    otherPath / 'ABI_{0}.{1}.dump'.format(fixtureLibBaseName, version),
                ])

            # Check that symlinks for compatible versions exist.
            if self.is_shared_libraries_config():

                twoDigitsVersionExtension = '.' + '.'.join(version.split('.')[0:2])
                symlinks.extend([
                    runtimeOutputDir / (testExeBaseName),
                    sharedLibOutputDir / (libBaseName + sharedLibExtension),
                    sharedLibOutputDir / (libBaseName + sharedLibExtension + twoDigitsVersionExtension),
                    sharedLibOutputDir / (fixtureLibBaseName + sharedLibExtension),
                    sharedLibOutputDir / (libBaseName + sharedLibExtension + twoDigitsVersionExtension)
                ])


        return [packageFiles, symlinks]


    def test_distributionPackages_MyLib_target(self):
        # Setup
        self.generate_project()
        target = DISTRIBUTION_PACKAGES_MYLIB_TARGET
        version = self.get_package_version('MyLib')
        system = self.osa.system()

        sources = [
            'Sources/MyLib/function.cpp'
        ]
        # Check the zip file is created.
        packageFileWE = 'MyLib.{0}.{1}.dev.{2}'.format(version, system, testprojectfixture.COMPILER_CONFIG)
        packageFileShort = packageFileWE + '.7z'
        packageFileDir = self.locations.get_full_path_config_makefile_folder(testprojectfixture.PARENT_CONFIG)  / 'html/Downloads/MyLib/LastBuild'
        output = [
            packageFileDir / packageFileShort
        ]

        # Execute
        self.do_basic_target_tests(target, target, source_files=sources, output_files=output)

        # Extract the zip file and check its content
        self.osa.execute_command_output(
            "cmake -E tar xzf " + packageFileShort,
            cwd=packageFileDir,
            print_output=miscosaccess.OutputMode.ON_ERROR
            )

        # Check the content of the package is correct.
        [package_files, package_symlinks] = self.get_expected_package_content(packageFileDir / packageFileWE / 'MyLib', version)
        self.assert_files_exist(package_files)
        self.assert_symlinks_exist(package_symlinks)


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
       


