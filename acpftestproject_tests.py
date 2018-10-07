"""
This module contains automated tests that operate on the ACPFTestProject project.
"""

import unittest
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

    def unpack_archive_package(self, package, packageGenerator, contentType):
        packageFileShort = self.get_distribution_package_short_name(package, packageGenerator, contentType)
        packageFileDir = self.get_distribution_package_directory(package)

        print( '------------------' + str(packageFileShort))

        self.osa.execute_command_output(
            "cmake -E tar xzf " + packageFileShort,
            cwd=packageFileDir,
            print_output=miscosaccess.OutputMode.ON_ERROR
            )

        packageFileWE = self.get_distribution_package_name_we(package, contentType)
        return  packageFileDir / packageFileWE / package


    def get_expected_package_content(self, prefix_dir, package, packageType):

        packageFiles = []
        symlinks = []

        config = testprojectfixture.COMPILER_CONFIG.lower()
        version = self.get_package_version(package)

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
        
        libBaseName = self.get_target_binary_base_name(package, testprojectfixture.COMPILER_CONFIG)
        testExeBaseName = self.get_target_binary_base_name( package + '_tests', testprojectfixture.COMPILER_CONFIG)
        fixtureLibBaseName = self.get_target_binary_base_name( package + '_fixtures', testprojectfixture.COMPILER_CONFIG)
        
        exeVersionPostfix = ''
        if self.is_linux():
            exeVersionPostfix += '-' + version

        sharedLibExtension = self.get_shared_lib_extension()
        staticLibExtension = self.get_static_lib_extension()
        exeExtension = self.get_exe_extension()
        versionExtension = '.' + version


        # Assemble pathes for package files.

        # CMake package files
        cmakeFilesPath = staticLibOutputDir / 'cmake' / package
        packageFiles.extend([
            cmakeFilesPath / (package + 'Config.cmake'),
            cmakeFilesPath / (package + 'ConfigVersion.cmake'),
            cmakeFilesPath / (package + 'Targets-{0}.cmake'.format(config)),
            cmakeFilesPath / (package + 'Targets.cmake'),
        ])

        # Public header files
        includePath = prefix_dir / 'include' / package
        packageFiles.extend([
            includePath / 'function.h',
            includePath / 'fixture.h',
            includePath / (package.lower() + '_export.h'),
            includePath / (package.lower() + '_tests_export.h'),
            includePath / 'cpfPackageVersion_{0}.h'.format(package)
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
                    sourcePath / 'cpfPackageVersion_{0}.h'.format(package),
                    sourcePath / 'fixture.cpp',
                    sourcePath / 'fixture.h',
                    sourcePath / 'function.cpp',
                    sourcePath / 'function.h',
                    sourcePath / (package.lower() + '_export.h'),
                    sourcePath / (package.lower() + '_tests_export.h')
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


    def test_distributionPackages_content(self):
        """
        This test verifies that the various package content type options
        lead to the correct package content.
        """
        # Execute
        self.generate_project()
        self.build_target('distributionPackages')

        # Verify the contents of the various packages.
        
        # developer library package
        package = 'CPackage'
        unpackedPackageDir = self.unpack_archive_package(package, '7Z', 'CT_DEVELOPER')
        [package_files, package_symlinks] = self.get_expected_package_content(unpackedPackageDir, package, 'LIB')
        self.assert_files_exist(package_files)
        self.assert_symlinks_exist(package_symlinks)






    
