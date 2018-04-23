#!/usr/bin/python3
"""
The entry point for running all tests of CPFTests.

The script requires two arguments.
1. A directory that can be used for writing files during tests.
2. A ";" separated list of files that are used for the project tests.
3. The cmake generator that should be used. This should be the same that is used for the current configuration.
4. CMake toolchain file. This should also be the same as the one from the current configuration.
"""

import sys
from pathlib import PureWindowsPath, PurePosixPath, PurePath

from Sources.CPFBuildscripts.python import miscosaccess
from Sources.CPFBuildscripts.python import filesystemaccess


def main(test_dir, project_test_files, generator, cmake_toolchain_file):

    run_project_tests(test_dir, project_test_files, generator, cmake_toolchain_file)


def run_project_tests(test_dir, project_test_files, generator, cmake_toolchain_file):

    # create test-file directory
    fsa = filesystemaccess.FileSystemAccess()
    test_dir = PurePath(test_dir).joinpath('CPFTest_ProjectTests')
    fsa.mkdirs(test_dir)

    # run the tests
    moa = miscosaccess.MiscOsAccess()
    cmake_command = "cmake -HSources/CPFTests/ProjectTests -B\"{0}\" -G\"{1}\" -DCMAKE_TOOLCHAIN_FILE=\"{2}\" -DTEST_FILES={3}".format(
        test_dir,
        generator, 
        cmake_toolchain_file,
        project_test_files)
    moa.execute_command(cmake_command)


    # delete test-file child directory
    fsa.rmtree(test_dir)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
