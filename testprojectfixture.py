#!/usr/bin/python3
"""
This module contains a testcase class the can be used to run tests
on a cpf test project.
"""

import os
import unittest
from pathlib import PurePosixPath
import shutil
import pprint
import hashlib
try:
    # installed with: pip install pypiwin32 on windows
    import win32api
except ImportError:
    bla = 'blub'

from Sources.CPFBuildscripts.python import miscosaccess
from Sources.CPFBuildscripts.python import filesystemaccess
from Sources.CPFBuildscripts.python import filelocations
from Sources.CPFBuildscripts.python import projectutils

BASE_TEST_DIR = ''
PARENT_CONFIG = ''
COMPILER_CONFIG = ''


def prepareTestProject(repository, project, cpf_cmake_dir, cpf_buildscripts_dir, instantiating_test_module):
    """
    This method clones a given repository of a CPF test project into the testdirectory 
    that is stored in the global BASE_TEST_DIR variable. After that it copies the
    current versions of CPFCMake and CPFBuildscripts into the test project, to make
    sure that the tests test the code that comes with this repository and not the
    the versions that are included in the test projects.

    To save time, test projects are only cloned once for all tests.
    All source files in the test project should be left unchanged to
    prevent coupling of single tests. All Generated files are deleted
    before each test, so they can be changed by test cases.

    The instantiating_test_module string is used to keep test-file directories for
    fixtures instances that run in parallel apart.
    """

    print('[{0}] Prepare test-project: {1}'.format(instantiating_test_module, project))

    fsa = filesystemaccess.FileSystemAccess()
    osa = miscosaccess.MiscOsAccess()

    # clone fresh project
    root_parent_dir = PurePosixPath(BASE_TEST_DIR).joinpath(instantiating_test_module)
    cpf_root_dir = root_parent_dir.joinpath(project)

    if fsa.exists(cpf_root_dir):
        # we remove remaining testfiles at the beginning of a test, so we
        # have the project still available for debugging if the test fails.
        fsa.rmtree(cpf_root_dir)
    fsa.mkdirs(root_parent_dir)
    osa.execute_command_output('git clone --recursive {0}'.format(repository), cwd=root_parent_dir, print_output=miscosaccess.OutputMode.ON_ERROR)
    
    # Replace the CPFCMake and CPFBuildscripts packages in the test project with the ones
    # that are used by this repository. This makes sure that we test the versions that
    # are used here and not the ones that are set in the test project.
    replace_package_in_test_project_with_local('CPFCMake', cpf_cmake_dir, cpf_root_dir)
    replace_package_in_test_project_with_local('CPFBuildscripts', cpf_buildscripts_dir, cpf_root_dir)
    return cpf_root_dir


def replace_package_in_test_project_with_local(package, rel_package_path, cpf_root_dir):
    """
    This function replaces a package in the cpf project situated at test_project_root_dir
    with the package of same name in this repository.
    """
    fsa = filesystemaccess.FileSystemAccess()
    osa = miscosaccess.MiscOsAccess()

    this_root_dir = PurePosixPath(os.path.dirname(os.path.realpath(__file__)) + "/../..")
    this_package_dir = this_root_dir.joinpath('Sources/{0}'.format(package))
    test_project_package_dir = cpf_root_dir.joinpath(rel_package_path)

    # move the .git file to a save place while the package content is replaces.
    gitFilePath = test_project_package_dir / ".git"
    tempGitFilePath = test_project_package_dir / "../.git"
    fsa.move(gitFilePath, tempGitFilePath)

    # We delete the package in the the copy the content of this package over
    fsa.rmtree(test_project_package_dir)
    shutil.copytree(str(this_package_dir), str(test_project_package_dir))

    # Move the .git file back in place.
    fsa.remove(gitFilePath)
    fsa.move(tempGitFilePath, gitFilePath)

    # We also commit and add the changes to make sure the repository is not dirty
    # which is expected after a "fresh" checkout. We have to call git add for the
    # case that we added files to the cpf projects, which are not picket up by
    # git commit only.
    osa.execute_command_output(
        'git add .',
        cwd=test_project_package_dir,
        print_output=miscosaccess.OutputMode.ON_ERROR
    )
    
    osa.execute_command_output(
        'git commit --allow-empty . -m "Set package content to local developer files."',
        cwd=test_project_package_dir,
        print_output=miscosaccess.OutputMode.ON_ERROR
    )

    osa.execute_command_output(
        'git commit --allow-empty . -m "Update {0}"'.format(package),
        cwd=cpf_root_dir,
        print_output=miscosaccess.OutputMode.ON_ERROR
    )



class TestProjectFixture(unittest.TestCase):
    """
    This fixture offers utilities for tests that work on checked out test projects.
    """
    def setUp(self, project, cpf_root_dir, cpf_cmake_dir, cpf_buildscripts_dir, ci_buildconfigurations_dir, instantiating_module):

        self.fsa = filesystemaccess.FileSystemAccess()
        self.osa = miscosaccess.MiscOsAccess()

        self.project = project
        self.cpf_root_dir = cpf_root_dir
        self.cpf_cmake_dir = cpf_cmake_dir
        self.cpf_buildscripts_dir = cpf_buildscripts_dir
        self.ci_buildconfigurations_dir = ci_buildconfigurations_dir
        self.instantiating_module = instantiating_module
        self.locations = filelocations.FileLocations(cpf_root_dir, cpf_cmake_dir, ci_buildconfigurations_dir )

        # add a big fat line to help with manual output parsing when an error occurs.
        if str(self._testMethodName) != "runTest":
            self.printPrefixed('-- Run test: {0}'.format(self._testMethodName))

    def printPrefixed(self, text):
        return print('[' + self.instantiating_module + '] ' + text)

    def copyScripts(self):
        self.run_python_command(self.cpf_buildscripts_dir + "/0_CopyScripts.py --CPFCMake_DIR \"{0}\" --CIBuildConfigurations_DIR \"{1}\" ".format(self.cpf_cmake_dir, self.ci_buildconfigurations_dir))

    def generate_project(self, d_options=[]):
        """
        Setup helper that runs all steps up to the generate step.
        Previously existing configurations or generated files are deleted.

        d_options can be a list of BLA=blub strings.

        """
        self.cleanup_generated_files()

        self.copyScripts()

        d_option_string = ''
        for option in d_options:
            d_option_string += '-D ' + option + ' '

        self.run_python_command('1_Configure.py {0} {1}'.format(PARENT_CONFIG, d_option_string))
        command = '2_Generate.py {0}'.format(PARENT_CONFIG)
        self.printPrefixed(command)
        self.run_python_command(command)

    def build_targets(self, targets):
        for target in targets:
            self.build_target(target)

    def build_target(self, target=None, config=None ):
        command = '3_Make.py'

        if target:
            command += ' --target {0}'.format(target)

        if self.is_visual_studio_config():
            if config:
                command += ' --config {0}'.format(config)
            else:
                command += ' --config {0}'.format(COMPILER_CONFIG)
        self.printPrefixed(command) # We do our own abbreviated command printing here.
        outputlist = self.run_python_command(command)
        return '\n'.join(outputlist)

    def cleanup_generated_files(self):
        # We delete all generated files to make sure they do not interfere with the test case.
        config_dir = self.cpf_root_dir.joinpath('Configuration')
        if self.fsa.exists(config_dir):
            self.fsa.rmtree(config_dir)

        generated_dir = self.cpf_root_dir.joinpath('Generated')
        if self.fsa.exists(generated_dir):
            self.fsa.rmtree(generated_dir)

    def run_python_command(self, argument, print_output=miscosaccess.OutputMode.ON_ERROR, print_command=False):
        """
        The function runs python3 on Linux and python on Windows.
        """
        system = self.osa.system()
        if system == 'Windows':
            return self.osa.execute_command_output(
                'python -u {0}'.format(argument), 
                cwd=self.cpf_root_dir, 
                print_output=print_output, 
                print_command=print_command 
                )
        elif system == 'Linux':
            # Force english language via environment variable,
            # so we can parse the output reliably.
            environment = os.environ
            environment['LANG'] = "en_US.UTF-8" 
            return self.osa.execute_command_output(
                'python3 -u {0}'.format(argument),
                cwd=self.cpf_root_dir,
                print_output=print_output,
                print_command=print_command,
                env=environment 
                )
        else:
            raise Exception('Unknown OS')


    def is_visual_studio_config(self):
        return PARENT_CONFIG == 'VS2019-shared-debug' or PARENT_CONFIG == 'VS2019-static-release'

    def is_visual_studio_debug_config(self):
        return PARENT_CONFIG == 'VS2019-shared-debug'

    def is_debug_compiler_config(self):
        return COMPILER_CONFIG == 'Debug'

    def is_release_compiler_config(self):
        return COMPILER_CONFIG == 'Release'

    def is_linux_debug_config(self):
        return PARENT_CONFIG == 'Gcc-shared-debug' or PARENT_CONFIG == 'Clang-shared-debug'

    def is_clang_config(self):
        return PARENT_CONFIG == 'Clang-static-release' or PARENT_CONFIG == 'Clang-shared-debug'

    def is_gcc_config(self):
        return PARENT_CONFIG == 'Gcc-shared-debug'

    def is_make_config(self):
        return PARENT_CONFIG == 'Clang-shared-debug' or PARENT_CONFIG == 'Gcc-shared-debug'

    def is_ninja_config(self):
        return PARENT_CONFIG == 'Clang-static-release'

    def is_make_config(self):
        return PARENT_CONFIG == 'Gcc-shared-debug' or PARENT_CONFIG == 'Clang-shared-debug'

    def is_msvc_or_debug_config(self):
        return self.is_visual_studio_config() or self.is_linux_debug_config()

    def is_windows(self):
        return self.osa.system() == 'Windows'

    def is_linux(self):
        return self.osa.system() == 'Linux'

    def is_shared_libraries_config(self):
        return PARENT_CONFIG == 'Gcc-shared-debug' or PARENT_CONFIG == 'Clang-shared-debug' or PARENT_CONFIG == 'VS2019-shared-debug'

    def get_compiler_configs(self):
        buildTypeKey = "CMAKE_BUILD_TYPE"                       # This should be defined for single config generators.
        configurationTypeKey = "CMAKE_CONFIGURATION_TYPES"      # This should be defined for multi config generators.
        
        # Get the values for both variables
        variableValues = self.get_cache_variable_values([configurationTypeKey, buildTypeKey])
        
        configValues = []
        if buildTypeKey in variableValues:
            assert(variableValues[buildTypeKey])                # It should have a value when it is defined.
            assert(configurationTypeKey not in variableValues)  # Only one of both should be defined.
            return [variableValues[buildTypeKey]]

        else:
            assert(configurationTypeKey in variableValues)
            return variableValues[configurationTypeKey].split(";")

    def get_cache_variable_values(self, variables):
        build_dir = self.locations.get_full_path_config_makefile_folder(PARENT_CONFIG)
        variablesOutputList = self.osa.execute_command_output(
            'cmake -LA -N -B.',
            cwd=build_dir,
            print_output=miscosaccess.OutputMode.ON_ERROR,
            print_command=False
        )
        
        return self.get_selected_variables_from_output_string(variablesOutputList, variables)


    def get_selected_variables_from_output_string(self, outputList, selectedVariables ):
        
        variableValueMap = {} 
        for line in outputList:
            splitLine = line.split('=')
            if len(splitLine) > 0:
                # in case of cache variables we have to remove the type
                variableFromLine = splitLine[0].split(':')[0]
                for variable in selectedVariables:
                    if variable == variableFromLine:
                        if len(splitLine) > 1:
                            variableValueMap[variable] = splitLine[1]
                        else:
                            variableValueMap[variable] = ""

        return variableValueMap


    def get_cmake_variables_in_file(self, variables, file):
        """
        Returns a map with the values of the given variables in the given cmake script file.
        """
        printVariablesScript = self.cpf_root_dir /  self.cpf_cmake_dir / "Scripts/printScriptFileVariables.cmake"
        variablesOutputList = self.osa.execute_command_output(
            'cmake -DSCRIPT_PATH="{0}" -P "{1}"'.format(str(file), printVariablesScript),
            cwd=self.cpf_root_dir,
            print_output=miscosaccess.OutputMode.ON_ERROR,
            print_command=False
        )

        return self.get_selected_variables_from_output_string(variablesOutputList, variables)

    def get_package_version(self, package):
        return projectutils.get_version_from_repository(self.cpf_root_dir, self.cpf_cmake_dir, package)

    def get_package_runtime_path_in_build_tree(self, config, compilerConfig):
        buildTreePath = self.locations.get_full_path_binary_output_folder(config, compilerConfig)
        if self.is_linux():
            return buildTreePath / 'bin'
        elif self.is_windows():
            return buildTreePath

        raise Exception('Unknown platform!. Add case.')

    def get_package_executable_path_in_build_tree(self, package, config, compilerConfig, version):
        runtimeDir = self.get_package_runtime_path_in_build_tree(config, compilerConfig)
        shortExeName = self.get_target_exe_shortname(package, compilerConfig, version)
        return runtimeDir / shortExeName

    def get_target_exe_shortname(self, target, compilerConfig, version):
        baseName = self.get_target_binary_base_name(target, compilerConfig)
        extension = self.get_exe_extension()
        if self.is_windows():
            return baseName + extension
        else:
            return baseName + '-' + version + extension

    def get_target_binary_base_name(self, target, compilerConfig):
        if self.is_release_compiler_config():
            return '{0}'.format(target)
        else:
            return '{0}-{1}'.format(target, compilerConfig.lower())

    def get_exe_extension(self):
        if self.is_linux():
            return ''
        elif self.is_windows():
            return '.exe'

        raise Exception('Unknown platform!. Add case.')

    def get_shared_lib_extension(self):
        if self.is_linux():
            return '.so'
        elif self.is_windows():
            return '.dll'

        raise Exception('Unknown platform!. Add case.')

    def get_static_lib_extension(self):
        if self.is_linux():
            return '.a'
        elif self.is_windows():
            return '.lib'

        raise Exception('Unknown platform!. Add case.')

    def get_package_executable_path(self, package, version, target_postfix=''):
        runtimeOutputDir = self.get_runtime_dir()
        exeBaseName = self.get_target_binary_base_name( package + target_postfix, COMPILER_CONFIG)
        exeVersionPostfix = self.get_exe_version_postfix(version)
        exeExtension = self.get_exe_extension()
        return runtimeOutputDir / (exeBaseName + exeVersionPostfix + exeExtension)

    def get_package_exe_symlink_path(self, package, version, target_postfix=''):
        runtimeOutputDir = self.get_runtime_dir()
        exeBaseName = self.get_target_binary_base_name( package + target_postfix, COMPILER_CONFIG)
        return runtimeOutputDir / exeBaseName

    def get_package_shared_lib_path(self, package, packageType, version, target_postfix=''):
        sharedLibOutputDir = self.get_shared_lib_dir()
        sharedLibShortName = self.get_shared_lib_short_name(package, packageType, version, target_postfix)
        return sharedLibOutputDir / sharedLibShortName

    def get_shared_lib_short_name(self, package, packageType, version, target_postfix=''):
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
        shortName = self.get_package_static_lib_short_name(package, packageType, target_postfix)
        return staticLibOutputDir / shortName

    def get_package_static_lib_short_name(self, package, packageType, target_postfix=''):
        libBaseName = self.get_package_lib_basename( package + target_postfix, packageType)
        libExtension = self.get_static_lib_extension()
        return libBaseName + libExtension

    def get_package_lib_basename(self, package, packageType):
        if self.is_exe_package(packageType):
            return self.get_target_binary_base_name('lib' + package, COMPILER_CONFIG)
        else:
            return self.get_target_binary_base_name(package, COMPILER_CONFIG)

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

    def get_full_distribution_package_path(self, package, packageGenerator, contentType, excludedTargets=[]):
        """
        Returns the full path to a package archive in the html-LastBuild download directory.
        """
        return self.get_distribution_package_directory(package, COMPILER_CONFIG, contentType, excludedTargets) / self.get_distribution_package_short_name(package, packageGenerator, contentType, excludedTargets)
       
    def get_distribution_package_directory(self, package, config, contentType, excludedTargets=[]):
        return self.locations.get_full_path_config_makefile_folder(PARENT_CONFIG)  / '{0}/_pckg/{1}/{2}'.format(package, config, self.get_content_type_path_string(contentType, excludedTargets))

    def get_distribution_package_short_name(self, package, packageGenerator, contentType, excludedTargets=[]):
        """
        Returns the short filename of the package file.
        """
        return self.get_distribution_package_name_we(package, COMPILER_CONFIG, contentType, excludedTargets) + '.' + self.get_distribution_package_extension(packageGenerator)

    def get_distribution_package_name_we(self, package, config, contentType, excludedTargets=[]):
        version = self.get_package_version(package)
        system = self.osa.system()
        contentTypeString = self.get_content_type_path_string(contentType, excludedTargets)
        
        if contentType == 'CT_SOURCES':
            return '{0}.{1}.{2}'.format(package ,version, contentTypeString)

        return '{0}.{1}.{2}.{3}.{4}'.format(package ,version, system, contentTypeString, config)

    def get_content_type_path_string(self, contentType, excludedTargets):
        if contentType == 'CT_RUNTIME':
            return 'runtime'
        elif contentType == 'CT_RUNTIME_PORTABLE':
            contentId = 'runtime-port'
            if excludedTargets:
                md5 = hashlib.md5(';'.join(excludedTargets).encode('utf-8')).hexdigest()
                contentId += '-' + md5[0:8]
            return contentId
        elif contentType == 'CT_DEVELOPER':
            return 'dev'
        elif contentType == 'CT_SOURCES':
            return 'src'
        else:
            raise Exception('Unknown content type "{0}"!'.format(contentType))

    def get_distribution_package_extension(self, packageGenerator):
        if packageGenerator == '7Z':
            return '7z'
        elif packageGenerator == 'ZIP':
            return 'zip'
        elif packageGenerator == 'TGZ':
            return 'tar.gz'
        else:
            raise Exception('Unhandled packageGenerator "{0}"'.format(packageGenerator))

    def get_distribution_package_install_directory(self):
        return self.locations.get_full_path_default_install_folder() / 'DistributionPackages'

    def assert_target_does_not_exist(self, target):
        target_misses_signature = ''
        if self.is_visual_studio_config():
            target_misses_signature = 'MSBUILD : error MSB1009:'
        elif self.is_make_config():
            target_misses_signature = '*** No rule to make target'
        elif self.is_ninja_config():
            target_misses_signature = 'ninja: error: unknown target'
        else:
            raise Exception('Error! Missing case for current configuration {0}.'.format(PARENT_CONFIG))
        
        with self.assertRaises(miscosaccess.CalledProcessError) as cm:
            # The reason to not print the output of the failing call ist, that MSBuild seems to parse
            # its own output to determine if an error happened. When a nested MSBuild call fails, the
            # parent call itself will also fail even if the nested call was supposed to fail like here.
            command = '3_Make.py --target {0}'.format(target)
            print(command) # We do our own abbreviated command printing here.
            self.run_python_command(command, print_output=miscosaccess.OutputMode.NEVER)
        # error MSB1009 says that a project is missing, which means the target does not exist.
        if not target_misses_signature in cm.exception.stdout:
            raise Exception('Test Error! Target {0} should not exist, but it did.'.format(target))
        

    def assert_targets_do_not_exist(self, targets):
        for target in targets:
            self.assert_target_does_not_exist(target)


    def assert_output_contains_signature(self, output, target, signature, trigger_source_file = None):
        """
        Builds the target and looks for the signature in its output.
        If the signature is not int the output it raises an exception.
        """
        missing_strings = self.find_missing_signature_strings(output, signature)
        if missing_strings:
            self.print_build_output(output)
            error_string= 'Test Error! Signature parts "{0}" were NOT found in build output of target {1}.'.format(missing_strings, target)
            if trigger_source_file:
                error_string = 'The build of target {0} was not triggered by touching file "{1}". The file does not seem to be one of the targets dependencies.'.format(target, trigger_source_file)
            raise Exception(error_string)

    def print_build_output(self, output):
        self.printPrefixed('------------------------- Start test-build output ------------------')
        print(output)
        self.printPrefixed('------------------------- End test-build output ------------------')

    def assert_output_has_not_signature(self, output, target, signature):
        """
        Builds the given target and raises an exception if the given signature
        can be found in the build output.
        """
        missing_strings = self.find_missing_signature_strings(output, signature)
        if not missing_strings:
            self.print_build_output(output)
            raise Exception('Test Error! Signature "{0}" was found in build output of target {1}.'.format(signature, target) )


    def find_missing_signature_strings(self, output, signature):
        missing_strings = []
        for string in signature:
            if not string in output:
                missing_strings.append(string)
        return missing_strings


    def assert_files_exist(self, files):
        """
        Throws an exception if not all files exist.
        File pathes must be relative to CMAKE_BINARY_DIR or absolute paths.
        """
        self.assert_filesystem_objects_exist(files, self.fsa.exists, 'files')


    def assert_symlinks_exist(self, symlinks):
        """
        Throws an exception if not all the given symlinks exist.
        This function only works on Linux.
        Paths must be relative to CMAKE_BINARY_DIR or absolute paths.
        """
        self.assert_filesystem_objects_exist(symlinks, os.path.islink, 'symlinks')


    def assert_filesystem_objects_exist(self, paths, object_checker, objects_name):
        missing_objects = []
        for path in paths:
            abs_path = path
            if not os.path.isabs(str(abs_path)):
                abs_path = self.locations.get_full_path_config_makefile_folder(PARENT_CONFIG) / abs_path

            if not object_checker(str(abs_path)):
                missing_objects.append(str(abs_path))

        if missing_objects:
            raise Exception('Test error! The following {0} were not produced as expected:\n{1}'.format(objects_name, '\n'.join(missing_objects)))


    def assert_files_do_not_exist(self, files):
        """
        Throws an exception if one of the given files exist. 
        File pathes must be relative to CMAKE_BINARY_DIR or absolute paths.
        """
        existing_files = []
        for file in files:
            full_file = file
            if not os.path.isabs(str(full_file)):
                full_file = self.locations.get_full_path_config_makefile_folder(PARENT_CONFIG) / file

            if self.fsa.exists(full_file):
                existing_files.append(str(full_file))

        if existing_files:
            raise Exception('Test error! The following files were unexpectedly produced:\n{1}'.format('\n'.join(existing_files)))


    def assert_filetree_is_equal(self, root_directory, files, symlinks=[]):
        """
        This function asserts that a root_directory contains exactly the given files and symlinks.
        The paths can be either relative to root_directory or absolute.
        """
        expectedFiles = self.get_rel_paths(root_directory, files)
        actualFiles = self.get_files_in_tree(root_directory)
        errorFiles = self.assert_filesystem_objects_are_equal(expectedFiles, actualFiles, 'files')

        expectedSymlinks = self.get_rel_paths(root_directory, symlinks)
        actualSymlinks = self.get_symlinks_in_tree(root_directory)
        errorSymlinks = self.assert_filesystem_objects_are_equal(expectedSymlinks, actualSymlinks, 'symlinks')

        if errorFiles or errorSymlinks:
            errorString = 'Test Error! Directory "{0}" did not contain the expected objects.\n'.format(str(root_directory)) + errorFiles + errorSymlinks
            raise Exception(errorString)
        

    def get_rel_paths(self, root_directory, paths):
        # Make all paths relative.
        relPaths = []
        for path in paths:
            if os.path.isabs(str(path)):
                relPaths.append(os.path.relpath(str(path), str(root_directory)))
            else:
                relPaths.append(path)
        return relPaths


    def get_files_in_tree(self, directory):
        return self.get_filsystem_objects_in_tree(directory, self.fsa.isfile )


    def get_symlinks_in_tree(self, directory):
        return self.get_filsystem_objects_in_tree(directory, os.path.islink )


    def get_filsystem_objects_in_tree(self, directory, object_checker):
        paths = self.get_paths_in_tree(directory)
        objects = []
        for path in paths:
            if object_checker(str( directory / path)):
                objects.append(path)

        return objects


    def get_paths_in_tree(self, directory):
        
        if not os.path.isdir(str(directory)):
            return []
        
        paths = os.listdir(str(directory))
        returnedPaths = []
        for path in paths:
            absSubDir = directory / path
            if os.path.isdir( str( absSubDir )):
                subPaths = self.get_paths_in_tree(absSubDir)
                for subPath in subPaths:
                    returnedPaths.append( path + '/' + subPath )
            else:
                returnedPaths.append(path)

        return returnedPaths


    def assert_filesystem_objects_are_equal(self, expected_objects, actual_objects, object_name_plural):
        """
        This assertion can be used to compare objects in a filesystem tree.
        """
        # Transform everything to strings.
        expected_objects = [ str(obj) for obj in expected_objects]
        actual_objects = [ str(obj) for obj in actual_objects]

        # Find the missing objects
        missing_objects = []
        for obj in expected_objects:
            if not obj in actual_objects:
                missing_objects.append(obj)

        errorStringMissing = ''
        if missing_objects:
            errorStringMissing = 'The folling expected {0} were missing:\n{1}'.format(object_name_plural, '\n'.join(missing_objects)) + '\n\n'

        # Find the objects that existed while they should not.
        unexpected_objects = []
        for obj in actual_objects:
            if not obj in expected_objects:
                unexpected_objects.append(obj)

        errorStringUnexpected = ''
        if unexpected_objects:
            errorStringUnexpected = 'The following {0} existed while they should not:\n{1}'.format(object_name_plural, '\n'.join(unexpected_objects)) + '\n\n'

        if missing_objects or unexpected_objects:
            return errorStringMissing + errorStringUnexpected
        else:
            return ''



def get_file_properties(fname):
    """
    Read all properties of the given file return them as a dictionary.
    """
    propNames = ('Comments', 'InternalName', 'ProductName',
        'CompanyName', 'LegalCopyright', 'ProductVersion',
        'FileDescription', 'LegalTrademarks', 'PrivateBuild',
        'FileVersion', 'OriginalFilename', 'SpecialBuild')

    props = {'FixedFileInfo': None, 'StringFileInfo': None, 'FileVersion': None}

    #try:

    # backslash as parm returns dictionary of numeric info corresponding to VS_FIXEDFILEINFO struc
    fixedInfo = win32api.GetFileVersionInfo(fname, '\\')
    props['FixedFileInfo'] = fixedInfo
    props['FileVersion'] = "%d.%d.%d.%d" % (fixedInfo['FileVersionMS'] / 65536,
            fixedInfo['FileVersionMS'] % 65536, fixedInfo['FileVersionLS'] / 65536,
            fixedInfo['FileVersionLS'] % 65536)

    # \VarFileInfo\Translation returns list of available (language, codepage)
    # pairs that can be used to retreive string info. We are using only the first pair.
    lang, codepage = win32api.GetFileVersionInfo(fname, '\\VarFileInfo\\Translation')[0]

    # any other must be of the form \StringfileInfo\%04X%04X\parm_name, middle
    # two are language/codepage pair returned from above
    strInfo = {}
    for propName in propNames:
        strInfoPath = u'\\StringFileInfo\\%04X%04X\\%s' % (lang, codepage, propName)
        strInfo[propName] = win32api.GetFileVersionInfo(fname, strInfoPath)

    props['StringFileInfo'] = strInfo

    #except:
        #pass

    return props