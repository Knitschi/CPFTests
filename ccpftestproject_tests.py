"""
This module contains automated tests that operate on the CCPFTestProject project.
"""

import unittest
from . import testprojectfixture
from pathlib import PureWindowsPath, PurePosixPath, PurePath

from Sources.CPFBuildscripts.python import miscosaccess


class CCPFTestProjectFixture(testprojectfixture.TestProjectFixture):
    """
    A fixture for tests that require a project with multiple
    internal and external packages.
    """

    cpf_root_dir = ''
    project = ''

    @classmethod
    def setUpClass(cls):
        cls.project = 'CCPFTestProject'
        cls.cpf_root_dir = testprojectfixture.prepareTestProject('https://github.com/Knitschi/CCPFTestProject.git', cls.project)


    def setUp(self):
        super(CCPFTestProjectFixture, self).setUp(self.project, self.cpf_root_dir)        

    def unpack_archive_package(self, package, packageGenerator, contentType, excludedTargets ):
        packageFileShort = self.get_distribution_package_short_name(package, packageGenerator, contentType, excludedTargets)
        packageFileDir = self.get_distribution_package_directory(package)

        self.osa.execute_command_output(
            "cmake -E tar xzf " + packageFileShort,
            cwd=packageFileDir,
            print_output=miscosaccess.OutputMode.ON_ERROR
            )

        packageFileWE = self.get_distribution_package_name_we(package, contentType, excludedTargets)
        return  packageFileDir / packageFileWE / package


    def get_expected_package_content(self, prefix_dir, package, contentType, packageType, packageNamespace, packageDependencies=[], packagePluginDependencies={}):
        """
        Returns absolute pathes to files and symlinks that are expected in the distribution package.
        """
        packageFiles = []
        symlinks = []

        # runtime package component
        if contentType == 'CT_RUNTIME' or contentType == 'CT_RUNTIME_PORTABLE' or contentType == 'CT_DEVELOPER':
            [packageFilesComponent, symlinksCompnent] = self.get_runtime_package_content(prefix_dir, package, packageType, packageNamespace)
            packageFiles.extend(packageFilesComponent)
            symlinks.extend(symlinksCompnent)

        # runtime dependencies component
        if contentType == 'CT_RUNTIME_PORTABLE':
            [packageFilesComponent, symlinksCompnent] = self.get_runtime_portable_package_content(prefix_dir, package, packageType, packageNamespace, packageDependencies, packagePluginDependencies)
            packageFiles.extend(packageFilesComponent)
            symlinks.extend(symlinksCompnent)

        # developer component
        if contentType == 'CT_DEVELOPER':
            [packageFilesComponent, symlinksCompnent] = self.get_developer_package_content(prefix_dir, package, packageType, packageNamespace)
            packageFiles.extend(packageFilesComponent)
            symlinks.extend(symlinksCompnent)

        # sources component
        if contentType == 'CT_SOURCES':
            [packageFilesComponent, symlinksCompnent] = self.get_sources_package_content(prefix_dir, package, packageType, packageNamespace)
            packageFiles.extend(packageFilesComponent)
            symlinks.extend(symlinksCompnent)
        
        return [packageFiles, symlinks]


    def get_runtime_package_content(self, prefix_dir, package, packageType, packageNamespace):
        """
        Returns the package files from the runtime install component.
        """
        packageFiles = []
        symlinks = []

        isExePackage = self.is_exe_package(packageType)
        version = self.get_package_version(package)

        # Executable
        if isExePackage:
            packageFiles.append( self.get_package_executable_path(prefix_dir, package, version) ) 

            # Symlink for executable
            if self.is_linux():
                symlinks.append( self.get_package_exe_symlink_path(prefix_dir, package, version) )
        else:
            # Shared library
            if self.is_shared_libraries_config():
                packageFiles.append( self.get_package_shared_lib_path(prefix_dir, package, packageType, version) )

                # Shared libary symlinks
                if self.is_linux():
                    symlinks.extend( self.get_package_shared_lib_symlink_paths(prefix_dir, package, packageType, version) )

        return [packageFiles, symlinks]


    def get_package_executable_path(self, prefix_dir, package, version, target_postfix=''):
        runtimeOutputDir = self.get_runtime_dir(prefix_dir)
        exeBaseName = self.get_target_binary_base_name( package + target_postfix, testprojectfixture.COMPILER_CONFIG)
        exeVersionPostfix = self.get_exe_version_postfix(version)
        exeExtension = self.get_exe_extension()
        return runtimeOutputDir / (exeBaseName + exeVersionPostfix + exeExtension)


    def get_package_exe_symlink_path(self, prefix_dir, package, version, target_postfix=''):
        runtimeOutputDir = self.get_runtime_dir(prefix_dir)
        exeBaseName = self.get_target_binary_base_name( package + target_postfix, testprojectfixture.COMPILER_CONFIG)
        return runtimeOutputDir / exeBaseName


    def get_package_shared_lib_path(self, prefix_dir, package, packageType, version, target_postfix=''):
        sharedLibOutputDir = self.get_shared_lib_dir(prefix_dir)
        sharedLibShortName = self.get_shared_lib_short_name(package, packageType, version, target_postfix)
        return sharedLibOutputDir / sharedLibShortName

    def get_shared_lib_short_name(self, package, packageType, version, target_postfix):
        libBaseName = self.get_package_lib_basename( package + target_postfix, packageType)
        libExtension = self.get_shared_lib_extension()
        versionExtension = self.get_version_extension(version)
        return libBaseName + libExtension + versionExtension


    def get_package_shared_lib_symlink_paths(self, prefix_dir, package, packageType, version, target_postfix=''):
        sharedLibOutputDir = self.get_shared_lib_dir(prefix_dir)
        libBaseName = self.get_package_lib_basename( package + target_postfix, packageType)
        libExtension = self.get_shared_lib_extension()
        twoDigitsVersionExtension = '.' + '.'.join(version.split('.')[0:2])

        noVersionSymlink = sharedLibOutputDir / (libBaseName + libExtension)
        mayourMinorVersionSymlink = sharedLibOutputDir / (libBaseName + libExtension + twoDigitsVersionExtension)
        
        return [ noVersionSymlink, mayourMinorVersionSymlink]


    def get_package_static_lib_path(self, prefix_dir, package, packageType, target_postfix=''):
        staticLibOutputDir = self.get_static_lib_dir(prefix_dir)
        libBaseName = self.get_package_lib_basename( package + target_postfix, packageType)
        libExtension = self.get_static_lib_extension()
        return staticLibOutputDir / (libBaseName + libExtension )


    def get_package_lib_basename(self, package, packageType):
        if self.is_exe_package(packageType):
            return self.get_target_binary_base_name('lib' + package, testprojectfixture.COMPILER_CONFIG)
        else:
            return self.get_target_binary_base_name(package, testprojectfixture.COMPILER_CONFIG)


    def get_version_extension(self, version):
        versionExtension = ''
        if self.is_linux():
            versionExtension = '.' + version
        return versionExtension


    def get_exe_version_postfix(self, version):
        exeVersionPostfix = ''
        if self.is_linux():
            exeVersionPostfix += '-' + version
        return exeVersionPostfix


    def get_runtime_dir(self, prefix_dir):
        if self.is_windows():
            return prefix_dir
        else:
            return prefix_dir / 'bin'


    def get_shared_lib_dir(self, prefix_dir):
        if self.is_windows():
            return prefix_dir
        else:
            return prefix_dir / 'lib'


    def get_static_lib_dir(self, prefix_dir):
        return prefix_dir / 'lib'


    def is_exe_package(self, packageType):
        return packageType == 'CONSOLE_APP' or packageType == 'GUI_APP'


    def get_runtime_portable_package_content(self, prefix_dir, package, packageType, packageNamespace, packageDependencies, packagePluginDependencies):
        """
        Returns the package files from the runtime-portable install component.
        """
        packageFiles = []
        symlinks = []

        # Shared external libraries
        if self.is_shared_libraries_config():
            for dependency in packageDependencies:

                version = self.get_package_version(dependency)
                packageFiles.append( self.get_package_shared_lib_path(prefix_dir, dependency, 'LIB', version) )

                # Shared libary symlinks
                #if self.is_linux():
                #    symlinks.extend( self.get_package_shared_lib_symlink_paths(prefix_dir, dependency, 'LIB', version) )

        # plugins
        for dir, targets in packagePluginDependencies.items():
            fullPluginDir = self.get_runtime_dir(prefix_dir) / dir
            for target in targets:
                version = self.get_package_version(target)
                libShortName = self.get_shared_lib_short_name(target, 'LIB', version, '')
                packageFiles.append( fullPluginDir / libShortName )


        return [packageFiles, symlinks]


    def get_developer_package_content(self, prefix_dir, package, packageType, packageNamespace):
        """
        Returns the package files from the developer install component.
        """
        packageFiles = []
        symlinks = []

        config = testprojectfixture.COMPILER_CONFIG.lower()
        version = self.get_package_version(package)
        isExePackage = self.is_exe_package(packageType)

        # Static library files
        if self.is_linux():
            if not self.is_shared_libraries_config():
                packageFiles.append(self.get_package_static_lib_path(prefix_dir, package, packageType))
        else:
            # we always have libs on windows
            packageFiles.append(self.get_package_static_lib_path(prefix_dir, package, packageType))


        # Implementation static libs for exe packages
        if isExePackage:
            packageFiles.append(self.get_package_static_lib_path(prefix_dir, package, packageType))


        # Test executable
        testPackageBaseName = package
        if isExePackage:
            testPackageBaseName = 'lib' + package

        packageFiles.append(self.get_package_executable_path(prefix_dir, testPackageBaseName, version, target_postfix='_tests'))
        # test exe  symlinks
        if self.is_linux():
            symlinks.append( self.get_package_exe_symlink_path(prefix_dir, testPackageBaseName, version, target_postfix='_tests') )


        # Fixture library files
        if self.is_shared_libraries_config() and not isExePackage:  # for exe packages the fixture lib is always static
            packageFiles.append(self.get_package_shared_lib_path(prefix_dir, package, packageType, version, target_postfix='_fixtures'))
            # libary symlinks
            if self.is_linux():
                symlinks.extend( self.get_package_shared_lib_symlink_paths(prefix_dir, package, packageType, version, target_postfix='_fixtures') )
        else:
            packageFiles.append(self.get_package_static_lib_path(prefix_dir, package, packageType, target_postfix='_fixtures'))


        # CMake package files
        cmakeFilesPath = self.get_static_lib_dir(prefix_dir) / 'cmake' / package
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
            includePath / (packageNamespace + '_export.h'),
            includePath / (packageNamespace + '_tests_export.h'),
            includePath / 'cpfPackageVersion_{0}.h'.format(package)
        ])


        # Pdb files and sources
        libBaseName = self.get_package_lib_basename(package, packageType)
        fixtureLibBaseName = self.get_package_lib_basename(package + '_fixtures', packageType)

        if self.is_windows():
            if self.is_debug_compiler_config():
                if self.is_shared_libraries_config() and not isExePackage:
                    sharedLibOutputDir = self.get_shared_lib_dir(prefix_dir)
                    packageFiles.extend([
                        sharedLibOutputDir / '{0}.pdb'.format(libBaseName),
                        sharedLibOutputDir / '{0}.pdb'.format(fixtureLibBaseName)
                    ])

                staticLibOutputDir = self.get_static_lib_dir(prefix_dir)
                testExeBaseName = self.get_package_lib_basename(package + '_tests', packageType)
                packageFiles.extend([
                    staticLibOutputDir / '{0}-compiler.pdb'.format(libBaseName),
                    staticLibOutputDir / '{0}-compiler.pdb'.format(fixtureLibBaseName),
                    staticLibOutputDir / '{0}-compiler.pdb'.format(testExeBaseName)
                ])

                # Source files are required for debugging with pdb files.
                sourcePath = prefix_dir / 'src' / package
                packageFiles.extend([
                    sourcePath / 'cpfPackageVersion_{0}.h'.format(package),
                    sourcePath / 'fixture.cpp',
                    sourcePath / 'fixture.h',
                    sourcePath / 'function.cpp',
                    sourcePath / 'function.h',
                    sourcePath / (packageNamespace + '_export.h'),
                    sourcePath / (packageNamespace + '_tests_export.h')
                ])


        # ABI dump files
        if self.is_linux() and not isExePackage: # dump files are only generated for libraries

            # Abi dumps
            otherPath = prefix_dir / 'other'
            if self.is_debug_compiler_config():
                packageFiles.extend([
                    otherPath / 'ABI_{0}.{1}.dump'.format(libBaseName, version),
                    otherPath / 'ABI_{0}.{1}.dump'.format(fixtureLibBaseName, version),
                ])


        return [packageFiles, symlinks]



    def get_sources_package_content(self, prefix_dir, package, packageType, packageNamespace):
        """
        Returns the package files from the sources install component.
        """
        packageFiles = []
        symlinks = []



        return [packageFiles, symlinks]


    def assert_APackage_content(self, contentType, excludedTargets=[]):
        package = 'APackage'
        unpackedPackageDir = self.unpack_archive_package(package, '7Z', contentType, excludedTargets)
        [package_files, package_symlinks] = self.get_expected_package_content(unpackedPackageDir, package, contentType, 'CONSOLE_APP', 'a', ['BPackage'], { 'plugins' : ['DPackage'] })
        self.assert_files_exist(package_files)
        self.assert_symlinks_exist(package_symlinks)


    def assert_BPackage_content(self, contentType, excludedTargets=[]):
        package = 'BPackage'
        unpackedPackageDir = self.unpack_archive_package(package, '7Z', contentType, excludedTargets )
        [package_files, package_symlinks] = self.get_expected_package_content(unpackedPackageDir, package, contentType, 'LIB', 'b')
        self.assert_files_exist(package_files)
        self.assert_symlinks_exist(package_symlinks)


    #####################################################################################################
    
    def test_distributionPackages_content(self):
        """
        This test verifies that the various package content type options
        lead to the correct package content.
        """
        # Execute
        self.generate_project()
        self.build_target('distributionPackages')

        # Verify the contents of the various packages.
        
        # runtime packages
        self.assert_APackage_content('CT_RUNTIME')
        self.assert_BPackage_content('CT_RUNTIME')

        # runtime portable packages
        excludedTargets = ['CPackage']
        self.assert_APackage_content('CT_RUNTIME_PORTABLE', excludedTargets)
        self.assert_BPackage_content('CT_RUNTIME_PORTABLE')

        # developer packages
        self.assert_APackage_content('CT_DEVELOPER')
        self.assert_BPackage_content('CT_DEVELOPER')

        # source packages
        #self.assert_APackage_content('CT_SOURCES')
        #self.assert_BPackage_content('CT_SOURCES')


