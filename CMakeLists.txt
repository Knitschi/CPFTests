include(cpfLocations)
include(cpfAddPackage)
include(cpfMiscUtilities)

cpfInitPackageProject(
	PACKAGE_NAME
	CPFT
)

set( files
    __init__.py
    acpftestproject_tests.py
    bcpftestproject_tests.py
    documentation/CPFTests.dox
    misc_tests.py
    ping.py
    run_tests.py
    simpleonelibcpftestproject_tests.py
    testprojectfixture.py
)

# Add the target.
cpfAddFilePackage(${PACKAGE_NAME} "${files}")


# Add a test target
set(dependedOnPackages CPFCMake CPFBuildscripts)
cpfAssertDefinedMessage(CPF_PARENT_CONFIG "Error! Your config file is missing a definition of variable CPF_PARENT_CONFIG")
# The CPFTESTS_TEST_NAME variable can be specified to run only a subset of all tests. Its value should be set in the developers config file.
# Running only one test is useful when adding new tests.
# Examples:
# CPFTESTS_TEST_NAME = ''                                                       -> run all tests
# CPFTESTS_TEST_NAME = 'misc_tests'                                             -> run all tests in the misc tests module
# CPFTESTS_TEST_NAME = 'misc_tests.ExcecuteCommandCase.test_execute_command'    -> runs only one test function
#
set(testScriptArgs  "test_dir=\"${CPF_TEST_FILES_DIR}/$<CONFIG>\" parent_config=${CPF_PARENT_CONFIG} compiler_config=$<CONFIG> test_name=${CPFTESTS_TEST_NAME}")
cpfAddRunPython3TestTarget( ${PACKAGE_NAME} run_tests.py ${testScriptArgs} "${files}" "${dependedOnPackages}" )
