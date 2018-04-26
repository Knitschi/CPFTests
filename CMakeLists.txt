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
cpfAddRunPython3TestTarget( ${PACKAGE_NAME} "run_tests.py" "\"${CPF_TEST_FILES_DIR}\" ${CPF_PARENT_CONFIG}" "${sources}" "${dependedOnPackages}" )
