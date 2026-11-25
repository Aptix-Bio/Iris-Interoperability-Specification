cmake_minimum_required(VERSION 3.25)
project(IrisInteroperabilitySpecification VERSION 0.1 LANGUAGES CXX)

option(I2S_BUILD_TESTS "Build the I2S tests" ${PROJECT_IS_TOP_LEVEL})

set(I2S_GENERATED_DIR "${CMAKE_CURRENT_SOURCE_DIR}/generated_source")

# The generator runs at every configure: it validates spec/*.json, enforces the
# append-only gate against tests/witness/witness.json, and writes
# generated_source/ and generated_docs/ (rewriting only files whose text
# changed). Editing a spec document, the generator or a source in include/
# (which I2S.hpp is stitched from) re-runs configure, so the header never lags
# what it comes from.
find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter)
execute_process(
    COMMAND "${Python3_EXECUTABLE}" -m generator -d "${CMAKE_CURRENT_SOURCE_DIR}"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    RESULT_VARIABLE I2S_GENERATOR_RESULT
)
if(NOT I2S_GENERATOR_RESULT EQUAL 0)
    message(FATAL_ERROR "I2S generator failed (exit ${I2S_GENERATOR_RESULT}); see its output above")
endif()
file(GLOB I2S_GENERATOR_INPUTS CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/spec/*.json"
    "${CMAKE_CURRENT_SOURCE_DIR}/generator/*.py"
    "${CMAKE_CURRENT_SOURCE_DIR}/generator/emit/*.py"
    "${CMAKE_CURRENT_SOURCE_DIR}/include/*.hpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/include/detail/*.hpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/witness/witness.json")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${I2S_GENERATOR_INPUTS})

# RTM SingleHeader_01, SingleHeader_03
# One header, I2S.hpp, generated from the vocabulary and the sources in
# include/. Only generated_source/ is on the include path, so the tests and the
# README examples compile against the header a consumer installs; the split
# sources in include/ are the generator's input.
include(GNUInstallDirs)
add_library(i2s INTERFACE)
add_library(I2S::i2s ALIAS i2s)
target_include_directories(i2s INTERFACE "$<BUILD_INTERFACE:${I2S_GENERATED_DIR}>"
    "$<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>")
target_compile_features(i2s INTERFACE cxx_std_20)

# The install: I2S.hpp into <prefix>/include, and a CMake package, so a
# consumer writes find_package(I2S) and links I2S::i2s.
include(CMakePackageConfigHelpers)
install(FILES "${I2S_GENERATED_DIR}/I2S.hpp" DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}")
install(TARGETS i2s EXPORT I2STargets)
install(EXPORT I2STargets NAMESPACE I2S:: DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/I2S")
# The package is the targets file alone: I2S depends on nothing to find.
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/I2SConfig.cmake" "include(\"\${CMAKE_CURRENT_LIST_DIR}/I2STargets.cmake\")\n")
# Before 1.0 a minor version may change what a key means, so a consumer asking
# for 0.1 accepts 0.1 alone.
write_basic_package_version_file("${CMAKE_CURRENT_BINARY_DIR}/I2SConfigVersion.cmake"
    COMPATIBILITY SameMinorVersion ARCH_INDEPENDENT)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/I2SConfig.cmake" "${CMAKE_CURRENT_BINARY_DIR}/I2SConfigVersion.cmake"
    DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/I2S")

# RTM Document_02
# The specification document, HTML and PDF, into <build>/doc. Not part of
# `all`: it needs Ruby and the Gemfile's Asciidoctor, and the gates run it as
# their last test.
if(PROJECT_IS_TOP_LEVEL)
    add_custom_target(i2s_document
        COMMAND "${CMAKE_COMMAND}" -DROOT=${CMAKE_CURRENT_SOURCE_DIR} -DOUT=${CMAKE_BINARY_DIR}/doc
                -P "${CMAKE_CURRENT_SOURCE_DIR}/cmake/render_document.cmake"
        COMMENT "Rendering the I2S specification into ${CMAKE_BINARY_DIR}/doc"
        VERBATIM)
endif()

if(I2S_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
