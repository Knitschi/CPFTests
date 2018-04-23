include(cpfLocations)
include(cpfAddPackage)

cpfInitPackageProject(
	PACKAGE_NAME
	CPFT
)

# Contains mid-level tests that are written in the CMake language,
# and require a project() call to work.
set( PROJECT_TESTS

)

# Contains high-level tests that are written in python and test
# the CPF from "outside"
set( INTEGRATION_TESTS

)

set( PYTHON_FILES
    run_tests.py
)

set( DOCUMENTATION_FILES
    documentation/CPFTests.dox
)

# Put the files in directories in visual studio.
source_group( ProjectTests FILES ${PROJECT_TESTS} )
source_group( IntegrationTests FILES ${INTEGRATION_TESTS} )
source_group( python FILES ${PYTHON_FILES} )
source_group( documentation FILES ${DOCUMENTATION_FILES} )

# Finally add the target.
set(sources ${PROJECT_TESTS} ${INTEGRATION_TESTS} ${PYTHON_FILES} ${DOCUMENTATION_FILES})

cpfAddFilePackage(${PACKAGE_NAME} "${sources}")

# Add a test target
cpfAddRunPython3TestTarget( ${PACKAGE_NAME} "run_tests.py \"${CPF_TEST_FILES_DIR}\" \"${sources}\" \"${CMAKE_GENERATOR}\" \"${CMAKE_TOOLCHAIN_FILE}\" )
