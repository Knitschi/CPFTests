include(cpfLocations)
include(cpfPackageProject)
include(cpfAddFilePackageComponent)
include(cpfMiscUtilities)

cpfPackageProject(
    TARGET_NAMESPACE cpftests
    COMPONENTS SINGLE_COMPONENT
    LANGUAGES NONE
)

set( testModules
    acpftestproject_tests.py
    bcpftestproject_tests.py
    ccpftestproject_tests.py
    misc_tests.py
    simpleonelibcpftestproject_tests1.py
    simpleonelibcpftestproject_tests2.py
    simpleonelibcpftestproject_tests3.py
    simpleonelibcpftestproject_tests4.py
    simpleonelibcpftestproject_tests5.py
)

set( files
    __init__.py
    documentation/CPFTests.rst
    ping.py
    README.md
    run_tests.py
    testprojectfixture.py
	simpleonelibcpftestprojectfixture.py
)

# Add the target.
cpfAddFilePackageComponent(SOURCES "${files};${testModules}")

# Add a test target
set(dependedOnPackages CPFCMake CPFBuildscripts)
cpfFindConfigFile(configFile ${CPF_CONFIG} TRUE "${CPFCMake_SOURCE_DIR}" "${CIBuildConfigurations_SOURCE_DIR}")
cpfAssertDefinedMessage(CPF_PARENT_CONFIG "Error! Your config file is missing a definition of variable CPF_PARENT_CONFIG")

# The CPFTESTS_TEST_NAME variable can be specified to run only a subset of all tests. Its value should be set in the developers config file.
# Running only one test is useful when adding new tests.
# Examples:
# set( CPFTESTS_TEST_NAME "test_execute_command" )     # -> runs only one test function
#set( CPFTESTS_TEST_NAME "CCPFTestProjectFixture" )     # -> runs all tests using the SimpleOneLibCPFTestProjectFixture
set( CPFTESTS_TEST_NAME "test_distributionPackages_content" )
set(testScriptArgs  "test_dir=\"${CPF_TEST_FILES_DIR}/$<CONFIG>\" parent_config=${CPF_PARENT_CONFIG} compiler_config=$<CONFIG> test_filter=${CPFTESTS_TEST_NAME}")
cpfAddRunPython3TestTargetForEachModule( run_tests.py "${testModules}" "${testScriptArgs}" "${files}" "${dependedOnPackages}" "${configFile}") # We also make this depend on the config file to make sure tests are retriggered when the CPFTESTS_TEST_NAME variable is changed.
