include(cpfLocations)
include(cpfAddPackage)

cpfInitPackageProject(
	PACKAGE_NAME
	CPFT
)

set( PYTHON_FILES
    TestProject_tests.py
    run_tests.py
    __init__.py
)

set( DOCUMENTATION_FILES
    documentation/CPFTests.dox
)

set( OTHER_FILES
)


# Put the files in directories in visual studio.
source_group( ProjectTests FILES ${PROJECT_TESTS} )
source_group( IntegrationTests FILES ${INTEGRATION_TESTS} )
source_group( python FILES ${PYTHON_FILES} )
source_group( documentation FILES ${DOCUMENTATION_FILES} )
source_group( Other FILES ${OTHER_FILES} )

# Finally add the target.
set(sources ${PYTHON_FILES} ${DOCUMENTATION_FILES} ${OTHER_FILES})

cpfAddFilePackage(${PACKAGE_NAME} "${sources}")

set(dependedOnPackages CPFCMake CPFBuildscripts)

# Add a test target
cpfAddRunPython3TestTarget( ${PACKAGE_NAME} "run_tests.py" "\"${CPF_TEST_FILES_DIR}\" ${CPF_PARENT_CONFIG}" "${sources}" "${dependedOnPackages}" )
