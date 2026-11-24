cmake_minimum_required(VERSION 3.25)
project(IrisInteroperabilitySpecification VERSION 0.1 LANGUAGES CXX)

option(I2S_BUILD_TESTS "Build the I2S tests" ${PROJECT_IS_TOP_LEVEL})

set(I2S_GENERATED_DIR "${CMAKE_CURRENT_SOURCE_DIR}/generated_source")

# The generator runs at every configure: it validates spec/*.json, enforces the
# append-only gate against tests/witness/witness.json, and writes
# generated_source/ and generated_docs/ (rewriting only files whose text
# changed). Editing a spec document or the generator re-runs configure, so the
# header never lags the JSON it comes from.
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
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/witness/witness.json")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${I2S_GENERATOR_INPUTS})

add_library(i2s INTERFACE)
add_library(I2S::i2s ALIAS i2s)
# The generated vocabulary (I2S_Keys.hpp) and the hand-written adapter over it
# (I2S_Attributes.hpp), both header-only.
target_include_directories(i2s INTERFACE "$<BUILD_INTERFACE:${I2S_GENERATED_DIR}>"
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>")
target_compile_features(i2s INTERFACE cxx_std_20)

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
