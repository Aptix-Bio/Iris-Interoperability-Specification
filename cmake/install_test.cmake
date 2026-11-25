# RTM SingleHeader_03
# Installs the build tree into a fresh prefix, checks that the one header it
# installs is I2S.hpp (beside the CMake package files), then configures,
# builds and runs tests/install against that prefix alone, so a consumer's
# view of I2S is what is tested.
#
#   cmake -DBINARY_DIR=<build> -DPREFIX=<dir> -DCONSUMER=<tests/install> -DCONSUMER_BINARY=<dir>
#         -DGENERATOR=<generator> -DCXX=<compiler> -P cmake/install_test.cmake
cmake_minimum_required(VERSION 3.25)

function(run)
    execute_process(COMMAND ${ARGV} RESULT_VARIABLE result OUTPUT_VARIABLE output ERROR_VARIABLE output)
    if(NOT result EQUAL 0)
        message("${output}")
        message(FATAL_ERROR "install_test: '${ARGV}' failed (exit ${result})")
    endif()
endfunction()

file(REMOVE_RECURSE "${PREFIX}" "${CONSUMER_BINARY}")
run("${CMAKE_COMMAND}" --install "${BINARY_DIR}" --prefix "${PREFIX}")

file(GLOB_RECURSE installed RELATIVE "${PREFIX}" "${PREFIX}/*")
list(FILTER installed EXCLUDE REGEX "^lib/cmake/I2S/I2S[A-Za-z-]*\\.cmake$")
if(NOT installed STREQUAL "include/I2S.hpp")
    message(FATAL_ERROR "install_test: the install must hold include/I2S.hpp and the package files only; found: ${installed}")
endif()

run("${CMAKE_COMMAND}" -S "${CONSUMER}" -B "${CONSUMER_BINARY}" -G "${GENERATOR}"
    "-DCMAKE_PREFIX_PATH=${PREFIX}" "-DCMAKE_CXX_COMPILER=${CXX}" -DCMAKE_BUILD_TYPE=Release)
run("${CMAKE_COMMAND}" --build "${CONSUMER_BINARY}")
run("${CONSUMER_BINARY}/i2s_install_consumer")
message(STATUS "install_test: a program built against ${PREFIX}/include/I2S.hpp alone ran")
