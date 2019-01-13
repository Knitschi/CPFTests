"""
This module contains automated tests that operate on the CCPFTestProject project.
"""

import unittest
from . import testprojectfixture
from pathlib import PureWindowsPath, PurePosixPath, PurePath
import pprint

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


    def get_expected_package_content(self, package, contentType, packageType, packageNamespace, packageDependencies=[], packagePluginDependencies={}):
        """
        Returns absolute pathes to files and symlinks that are expected in the distribution package.
        """
        # runtime package component
        if contentType == 'CT_RUNTIME':
            return self.get_runtime_package_content(package, packageType, packageNamespace)

        # runtime dependencies component
        if contentType == 'CT_RUNTIME_PORTABLE':
            return self.get_runtime_portable_package_content(package, packageType, packageNamespace, packageDependencies, packagePluginDependencies)

        # developer component
        if contentType == 'CT_DEVELOPER':
            return self.get_developer_package_content(package, packageType, packageNamespace)

        # sources component
        if contentType == 'CT_SOURCES':
            return self.get_sources_package_content(package, packageType, packageNamespace)
        
        raise Exception("Missing case!")

        return []


    def get_runtime_package_content(self, package, packageType, packageNamespace):
        """
        Returns the package files from the runtime install component.
        """
        # Interface libraries have no runtime files.
        isNotInterfaceLib = self.is_not_interface_lib(packageType)
        if not isNotInterfaceLib:
            return [[],[]]

        packageFiles = []
        symlinks = []

        isExePackage = self.is_exe_package(packageType)
        version = self.get_package_version(package)

        # Executable
        if isExePackage:
            
            # package executable
            packageFiles.append( self.get_package_executable_path(package, version) ) 

            # Symlink for executable
            # I could not find a way to suppress the generation of the name-link
            # for executables. So this is always expected.
            if self.is_linux():
                symlinks.append( self.get_package_exe_symlink_path(package, version) )

        # Production library
        if self.is_shared_libraries_config():
            packageFiles.append( self.get_package_shared_lib_path(package, packageType, version) )

                # Shared libary symlinks
                #if self.is_linux():
                #    symlinks.extend( self.get_package_shared_lib_symlink_paths(package, packageType, version) )

        return [packageFiles, symlinks]


    def get_package_executable_path(self, package, version, target_postfix=''):
        runtimeOutputDir = self.get_runtime_dir()
        exeBaseName = self.get_target_binary_base_name( package + target_postfix, testprojectfixture.COMPILER_CONFIG)
        exeVersionPostfix = self.get_exe_version_postfix(version)
        exeExtension = self.get_exe_extension()
        return runtimeOutputDir / (exeBaseName + exeVersionPostfix + exeExtension)


    def get_package_exe_symlink_path(self, package, version, target_postfix=''):
        runtimeOutputDir = self.get_runtime_dir()
        exeBaseName = self.get_target_binary_base_name( package + target_postfix, testprojectfixture.COMPILER_CONFIG)
        return runtimeOutputDir / exeBaseName


    def get_package_shared_lib_path(self, package, packageType, version, target_postfix=''):
        sharedLibOutputDir = self.get_shared_lib_dir()
        sharedLibShortName = self.get_shared_lib_short_name(package, packageType, version, target_postfix)
        return sharedLibOutputDir / sharedLibShortName

    def get_shared_lib_short_name(self, package, packageType, version, target_postfix):
        libBaseName = self.get_package_lib_basename( package + target_postfix, packageType)
        libExtension = self.get_shared_lib_extension()
        versionExtension = self.get_version_extension(version)
        return libBaseName + libExtension + versionExtension


    def get_package_shared_lib_symlink_paths(self, package, packageType, version, target_postfix=''):
        sharedLibOutputDir = self.get_shared_lib_dir()
        libBaseName = self.get_package_lib_basename( package + target_postfix, packageType)
        libExtension = self.get_shared_lib_extension()
        twoDigitsVersionExtension = '.' + '.'.join(version.split('.')[0:2])

        noVersionSymlink = sharedLibOutputDir / (libBaseName + libExtension)
        mayourMinorVersionSymlink = sharedLibOutputDir / (libBaseName + libExtension + twoDigitsVersionExtension)
        
        return [ noVersionSymlink, mayourMinorVersionSymlink]


    def get_package_static_lib_path(self, package, packageType, target_postfix=''):
        staticLibOutputDir = self.get_static_lib_dir()
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


    def get_runtime_dir(self):
        if self.is_windows():
            return PurePosixPath('')
        else:
            return PurePosixPath('bin')


    def get_shared_lib_dir(self):
        if self.is_windows():
            return PurePosixPath('')
        else:
            return PurePosixPath('lib')


    def get_static_lib_dir(self):
        return PurePosixPath('lib')


    def is_exe_package(self, packageType):
        return packageType == 'CONSOLE_APP' or packageType == 'GUI_APP'


    def is_not_interface_lib(self, packageType):
        return not (packageType == 'INTERFACE_LIB')


    def get_runtime_portable_package_content(self, package, packageType, packageNamespace, packageDependencies, packagePluginDependencies):
        """
        Returns the package files from the runtime-portable install component.
        """
        [packageFiles, symlinks] = self.get_runtime_package_content(package, packageType, packageNamespace)

        # Shared external libraries
        if self.is_shared_libraries_config():
            for dependency in packageDependencies:

                version = self.get_package_version(dependency)
                packageFiles.append( self.get_package_shared_lib_path(dependency, 'LIB', version) )

        # plugins
        for dir, targets in packagePluginDependencies.items():
            fullPluginDir = self.get_runtime_dir() / dir
            for target in targets:
                version = self.get_package_version(target)
                libShortName = self.get_shared_lib_short_name(target, 'LIB', version, '')
                packageFiles.append( fullPluginDir / libShortName )


        return [packageFiles, symlinks]


    def get_developer_package_content(self, package, packageType, packageNamespace):
        """
        Returns the package files from the developer install component.
        """
        config = testprojectfixture.COMPILER_CONFIG.lower()
        version = self.get_package_version(package)
        isExePackage = self.is_exe_package(packageType)
        isNotInterfaceLib = self.is_not_interface_lib(packageType)
        isInterfaceLib = not isNotInterfaceLib

        # The developer package also contains the main binaries.
        [packageFiles, symlinks] = self.get_runtime_package_content(package, packageType, packageNamespace)

        # We have to add the static libraries for the developer package.
        if isNotInterfaceLib:   # Interface libraries have no binary files.
            # Main binary file
            if isExePackage:
                # Implementation libs for exe packages
                if self.is_shared_libraries_config():
                    if self.is_visual_studio_config():
                        # We get an additional libs for the implementation dlls with msvc
                        packageFiles.append(self.get_package_static_lib_path(package, packageType))
                else:
                    # The static implementation lib
                    packageFiles.append(self.get_package_static_lib_path(package, packageType))
            else:
                if self.is_shared_libraries_config():
                    if self.is_visual_studio_config():
                        # We get additional libs for dlls with msvc
                        packageFiles.append(self.get_package_static_lib_path(package, packageType))
                else:
                    # Add the static main library.
                    packageFiles.append(self.get_package_static_lib_path(package, packageType))

        # Test executable
        testPackageBaseName = package
        if isExePackage:
            testPackageBaseName = 'lib' + package
        packageFiles.append(self.get_package_executable_path(testPackageBaseName, version, target_postfix='_tests'))
        
        # test exe  symlinks
        if self.is_linux():
            symlinks.append( self.get_package_exe_symlink_path(testPackageBaseName, version, target_postfix='_tests') )

        # Fixture library files
        if self.is_shared_libraries_config():
            packageFiles.append(self.get_package_shared_lib_path(package, packageType, version, target_postfix='_fixtures'))
            # We get additional libs for dlls with msvc
            if self.is_visual_studio_config():
                packageFiles.append(self.get_package_static_lib_path(package, packageType, target_postfix='_fixtures'))
        else:
            packageFiles.append(self.get_package_static_lib_path(package, packageType, target_postfix='_fixtures'))

        # CMake package files
        cmakeFilesPath = self.get_static_lib_dir() / 'cmake' / package
        packageFiles.extend([
            cmakeFilesPath / (package + 'Config.cmake'),
            cmakeFilesPath / (package + 'ConfigVersion.cmake'),
            cmakeFilesPath / (package + 'Targets-{0}.cmake'.format(config)),
            cmakeFilesPath / (package + 'Targets.cmake'),
        ])

        # Public header files
        includePath = PurePosixPath('include') / package
        packageFiles.extend([
            includePath / 'function.h',
            includePath / 'Tests/fixture.h',
            includePath / (packageNamespace + '_tests_export.h'),
            includePath / 'cpfPackageVersion_{0}.h'.format(package)
        ])

        if isNotInterfaceLib:   # Interface libs do not need an export macro header.
            packageFiles.append( includePath / (packageNamespace + '_export.h'))

        if package == 'APackage':
            packageFiles.append( includePath / 'Tests/generatedHeader.h' )

        # Pdb files and sources
        libBaseName = self.get_package_lib_basename(package, packageType)
        fixtureLibBaseName = self.get_package_lib_basename(package + '_fixtures', packageType)

        if self.is_visual_studio_config():
            if self.is_debug_compiler_config():

                exeBaseName = self.get_target_binary_base_name( package , testprojectfixture.COMPILER_CONFIG)
                testExeBaseName = self.get_package_lib_basename(package + '_tests', packageType)
                runtimeOutputDir = self.get_runtime_dir()
                staticLibOutputDir = self.get_static_lib_dir()

                # linker pdb files
                if self.is_shared_libraries_config():
                    sharedLibOutputDir = self.get_shared_lib_dir()
                    if isNotInterfaceLib:
                        packageFiles.append(sharedLibOutputDir / '{0}.pdb'.format(libBaseName))
                    packageFiles.append(sharedLibOutputDir / '{0}.pdb'.format(fixtureLibBaseName))

                if isExePackage:
                    packageFiles.append( runtimeOutputDir / '{0}.pdb'.format(exeBaseName))
                    packageFiles.append( staticLibOutputDir / '{0}-compiler.pdb'.format(exeBaseName))
                
                packageFiles.append(runtimeOutputDir / '{0}.pdb'.format(testExeBaseName))

                # compiler pdb for libraries
                if isNotInterfaceLib:
                    packageFiles.append(staticLibOutputDir / '{0}-compiler.pdb'.format(libBaseName))

                packageFiles.extend([
                    staticLibOutputDir / '{0}-compiler.pdb'.format(fixtureLibBaseName),
                    staticLibOutputDir / '{0}-compiler.pdb'.format(testExeBaseName)
                ])

                # Source files are required for debugging with pdb files.
                allSources = self.get_package_source_files(package, packageType, packageNamespace)
                cppSources = []
                # The component will only install the h and cpp files.
                cppExtensions = ['.cpp', '.h']
                for source in allSources:
                    if source.suffix in cppExtensions:
                        cppSources.append(source)

                # The interface library does not install any source files because
                # they are all public headers and availabe in the include directory.
                sourcePath = PurePosixPath('src') / package
                if isInterfaceLib:
                    cppSources.remove(sourcePath / 'function.h')
                    cppSources.remove(sourcePath / 'cpfPackageVersion_{0}.h'.format(package))

                packageFiles.extend(cppSources)


        # ABI dump files
        if self.is_linux() and not isExePackage: # dump files are only generated for libraries

            # Abi dumps (interface libs have no binaries so no dumps are created)
            otherPath = PurePosixPath('other')
            if self.is_debug_compiler_config() and isNotInterfaceLib:
                packageFiles.extend([
                    otherPath / 'ABI_{0}.{1}.dump'.format(libBaseName, version),
                    otherPath / 'ABI_{0}.{1}.dump'.format(fixtureLibBaseName, version),
                ])

        return [packageFiles, symlinks]


    def get_sources_package_content(self, package, packageType, packageNamespace):
        """
        Returns the package files from the sources install component.
        """
        packageFiles = []
        symlinks = []

        packageFiles = self.get_package_source_files(package, packageType, packageNamespace)

        return [packageFiles, symlinks]


    def get_package_source_files(self, package, packageType, packageNamespace):

        isInterfaceLib = not self.is_not_interface_lib(packageType)

        sourceFiles = []

        sourcePath = PurePosixPath('src') / package
        sourceFiles.extend([
            sourcePath / 'CMakeLists.txt',
            sourcePath / 'cpfPackageVersion_{0}.cmake'.format(package),
            sourcePath / 'cpfPackageVersion_{0}.h'.format(package),
            sourcePath / 'function.cpp',
            sourcePath / 'function.h',
            sourcePath / 'Tests/fixture.cpp',
            sourcePath / 'Tests/fixture.h',
            sourcePath / 'Tests/tests_main.cpp',
            sourcePath / (packageNamespace + '_export.h'),
            sourcePath / (packageNamespace + '_tests_export.h')
        ])

        # The interface library has no cpp file and export macro header
        if isInterfaceLib:
            sourceFiles.remove( sourcePath / 'function.cpp')
            sourceFiles.remove( sourcePath / (packageNamespace + '_export.h'))

        # The generated header is only in APackage
        if package == 'APackage':
            sourceFiles.append( sourcePath / 'Tests/generatedHeader.h' )

        if self.is_exe_package(packageType):
            sourceFiles.extend([
                sourcePath / 'main.cpp',
            ])

        return sourceFiles


    def assert_APackage_content(self, contentType, excludedTargets=[]):
        package = 'APackage'
        unpackedPackageDir = self.unpack_archive_package(package, '7Z', contentType, excludedTargets)
        [package_files, package_symlinks] = self.get_expected_package_content(package, contentType, 'CONSOLE_APP', 'a', ['BPackage'], { 'plugins' : ['DPackage'] })
        self.assert_filetree_is_equal( unpackedPackageDir , package_files, package_symlinks)


    def assert_BPackage_content(self, contentType, excludedTargets=[]):
        package = 'BPackage'
        unpackedPackageDir = self.unpack_archive_package(package, '7Z', contentType, excludedTargets )
        [package_files, package_symlinks] = self.get_expected_package_content(package, contentType, 'LIB', 'b')
        self.assert_filetree_is_equal( unpackedPackageDir , package_files, package_symlinks)


    def assert_EPackage_content(self, contentType, excludedTargets=[]):
        package = 'EPackage'
        unpackedPackageDir = self.unpack_archive_package(package, '7Z', contentType, excludedTargets )
        [package_files, package_symlinks] = self.get_expected_package_content(package, contentType, 'INTERFACE_LIB', 'e')
        self.assert_filetree_is_equal( unpackedPackageDir , package_files, package_symlinks)


    #####################################################################################################
    
    def test_distributionPackages_content(self):
        """
        This test verifies that the various package content type options
        lead to the correct package content.
        """
        # Execute
        self.generate_project()
        self.build_target('distributionPackages')


        # Verify all packages were created.
        # We only check APackage packages, because the other use the same code.
        expectedDistPackageFiles = []
        expectedDistPackageFiles.append(self.get_distribution_package_short_name('APackage', '7Z', 'CT_RUNTIME'))
        expectedDistPackageFiles.append(self.get_distribution_package_short_name('APackage', 'ZIP', 'CT_RUNTIME'))
        expectedDistPackageFiles.append(self.get_distribution_package_short_name('APackage', 'TGZ', 'CT_RUNTIME'))
        expectedDistPackageFiles.append(self.get_distribution_package_short_name('APackage', '7Z', 'CT_RUNTIME_PORTABLE', ['CPackage']))
        expectedDistPackageFiles.append(self.get_distribution_package_short_name('APackage', '7Z', 'CT_DEVELOPER'))
        expectedDistPackageFiles.append(self.get_distribution_package_short_name('APackage', '7Z', 'CT_SOURCES'))
        packageFileDir = self.get_distribution_package_directory('APackage')
        self.assert_filetree_is_equal( packageFileDir , expectedDistPackageFiles)


        # Verify the contents of the various packages.

        # runtime packages
        print('-- assert runtime packages')
        self.assert_APackage_content('CT_RUNTIME')
        self.assert_BPackage_content('CT_RUNTIME')

        # runtime portable packages
        print('-- assert runtime portable packages')
        excludedTargets = ['CPackage']
        self.assert_APackage_content('CT_RUNTIME_PORTABLE', excludedTargets)
        self.assert_BPackage_content('CT_RUNTIME_PORTABLE')

        # developer packages
        print('-- assert developer packages')
        self.assert_APackage_content('CT_DEVELOPER')
        self.assert_BPackage_content('CT_DEVELOPER')
        self.assert_EPackage_content('CT_DEVELOPER')

        # source packages
        print('-- assert source packages')
        self.assert_APackage_content('CT_SOURCES')
        self.assert_BPackage_content('CT_SOURCES')
        self.assert_EPackage_content('CT_SOURCES')


