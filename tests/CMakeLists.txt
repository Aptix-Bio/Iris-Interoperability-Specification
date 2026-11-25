include(FetchContent)
# Catch2 is built at the tests' standard, so its string_view support (which it
# compiles only under C++17 and later) links with tests that print one.
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
# Fetched into the gitignored dependencies/ beside the sources, so every build
# tree shares one copy, pinned by version and archive hash: a re-tagged release
# fails the hash instead of changing the tests' framework underneath them.
# Catch2 v3.16.1, released 2026-10-08 (https://github.com/catchorg/Catch2/releases/tag/v3.16.1, read 2026-11-24).
if(PROJECT_IS_TOP_LEVEL)
    set(FETCHCONTENT_BASE_DIR "${PROJECT_SOURCE_DIR}/dependencies")
endif()
FetchContent_Declare(Catch2
    URL https://github.com/catchorg/Catch2/archive/refs/tags/v3.16.1.tar.gz
    URL_HASH SHA256=d16bd1b8b2364918bd472cb216394acb93bde6784890df0d91bccfb3f28d777d
    DOWNLOAD_EXTRACT_TIMESTAMP ON
)
FetchContent_MakeAvailable(Catch2)

# RTM Generated_01, Generated_02, Generated_03
add_executable(i2s_keys_tests cpp/keys_tests.cpp)
target_link_libraries(i2s_keys_tests PRIVATE I2S::i2s Catch2::Catch2WithMain)
target_compile_options(i2s_keys_tests PRIVATE
    $<IF:$<CXX_COMPILER_ID:MSVC>,/W4 /WX,-Wall -Wextra -Wpedantic -Werror>)
add_test(NAME i2s_keys_tests COMMAND i2s_keys_tests)

# RTM TypedKeys_01, Encoding_01, Adapter_01, Iteration_01, PhiFlag_02
add_executable(i2s_attributes_tests cpp/attributes_tests.cpp)
target_link_libraries(i2s_attributes_tests PRIVATE I2S::i2s Catch2::Catch2WithMain)
target_compile_options(i2s_attributes_tests PRIVATE
    $<IF:$<CXX_COMPILER_ID:MSVC>,/W4 /WX,-Wall -Wextra -Wpedantic -Werror>)
add_test(NAME i2s_attributes_tests COMMAND i2s_attributes_tests)

# RTM TypedKeys_01
# A value of the wrong type must not compile, and the compiler must say why:
# each case names the concept the value failed, or the unknown key.
set(compile_fail_text_to_date_time "DateTimeValue")
set(compile_fail_int_to_text "TextValue")
set(compile_fail_int_to_boolean "BooleanValue")
set(compile_fail_unknown_key "NoSuchKey")
# RTM ReadableHeaders_01
# The flat spelling I2S::Manufacturer was replaced by I2S::Attribute::Manufacturer.
set(compile_fail_flat_spelling "Manufacturer")
foreach(case text_to_date_time int_to_text int_to_boolean unknown_key flat_spelling)
    add_executable(i2s_compile_fail_${case} EXCLUDE_FROM_ALL cpp/compile_fail/${case}.cpp)
    target_link_libraries(i2s_compile_fail_${case} PRIVATE I2S::i2s)
    add_test(NAME i2s_compile_fail_${case}
        COMMAND "${CMAKE_COMMAND}" -DBINARY_DIR=${CMAKE_BINARY_DIR} -DTARGET=i2s_compile_fail_${case}
                "-DEXPECT=${compile_fail_${case}}" -P "${PROJECT_SOURCE_DIR}/cmake/expect_compile_error.cmake")
endforeach()

# RTM SingleHeader_02
# Two translation units, one defining I2S_IMPLEMENTATION: the program links
# only when every non-template function of I2S.hpp is defined exactly once.
add_executable(i2s_two_units cpp/two_units/with_implementation.cpp cpp/two_units/other_unit.cpp)
target_link_libraries(i2s_two_units PRIVATE I2S::i2s)
target_compile_options(i2s_two_units PRIVATE
    $<IF:$<CXX_COMPILER_ID:MSVC>,/W4 /WX,-Wall -Wextra -Wpedantic -Werror>)
add_test(NAME i2s_two_units COMMAND i2s_two_units)

# RTM SingleHeader_02
# A program in which no translation unit defines I2S_IMPLEMENTATION fails to
# link, and the linker names the I2S function it found no body for.
add_executable(i2s_missing_implementation EXCLUDE_FROM_ALL cpp/missing_implementation.cpp)
target_link_libraries(i2s_missing_implementation PRIVATE I2S::i2s)
add_test(NAME i2s_missing_implementation_fails_to_link
    COMMAND "${CMAKE_COMMAND}" -DBINARY_DIR=${CMAKE_BINARY_DIR} -DTARGET=i2s_missing_implementation
            "-DEXPECT=I2S::Attributes::to_pairs" -P "${PROJECT_SOURCE_DIR}/cmake/expect_compile_error.cmake")

# RTM SingleHeader_03
# The install: only I2S.hpp and the package files, and a program built against
# the install prefix alone.
add_test(NAME i2s_install
    COMMAND "${CMAKE_COMMAND}" -DBINARY_DIR=${CMAKE_BINARY_DIR} -DPREFIX=${CMAKE_CURRENT_BINARY_DIR}/install_prefix
            -DCONSUMER=${CMAKE_CURRENT_SOURCE_DIR}/install -DCONSUMER_BINARY=${CMAKE_CURRENT_BINARY_DIR}/install_consumer
            "-DGENERATOR=${CMAKE_GENERATOR}" -DCXX=${CMAKE_CXX_COMPILER}
            -P "${PROJECT_SOURCE_DIR}/cmake/install_test.cmake")

# RTM Readme_01
# The README's C++ examples, compiled and run.
set(readme_source "${CMAKE_CURRENT_BINARY_DIR}/readme_examples.cpp")
execute_process(
    COMMAND "${CMAKE_COMMAND}" -DREADME=${PROJECT_SOURCE_DIR}/README.md -DOUT=${readme_source}
            -P "${PROJECT_SOURCE_DIR}/cmake/readme_examples.cmake"
    RESULT_VARIABLE readme_result)
if(NOT readme_result EQUAL 0)
    message(FATAL_ERROR "README examples could not be extracted (exit ${readme_result})")
endif()
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${PROJECT_SOURCE_DIR}/README.md")
add_executable(i2s_readme_examples "${readme_source}")
target_link_libraries(i2s_readme_examples PRIVATE I2S::i2s)
target_compile_options(i2s_readme_examples PRIVATE
    $<IF:$<CXX_COMPILER_ID:MSVC>,/W4 /WX,-Wall -Wextra -Wpedantic -Werror>)
add_test(NAME i2s_readme_examples COMMAND i2s_readme_examples)

# RTM Generated_04
# A key renamed in the JSON must break every use of its old name at compile
# time. The source is built by a test, outside `all`, and the test passes only
# when the compiler's error names the missing enumerator.
add_executable(i2s_renamed_key EXCLUDE_FROM_ALL cpp/renamed_key.cpp)
target_link_libraries(i2s_renamed_key PRIVATE I2S::i2s)
add_test(NAME i2s_renamed_key_fails_to_compile
    COMMAND "${CMAKE_COMMAND}" --build "${CMAKE_BINARY_DIR}" --target i2s_renamed_key --config $<CONFIG>)
set_tests_properties(i2s_renamed_key_fails_to_compile PROPERTIES
    PASS_REGULAR_EXPRESSION "error[^\n]*DigitalSlideIdentifier")

# RTM Gates_01
# The gates, in the order they run: the linter, the generator check, the tests,
# the document render. `cmake --workflow --preset gates` configures, builds and
# runs them; DEPENDS fixes the order whatever ctest's cost data says. The
# Python checks run through uv in the project's locked environment.
find_program(I2S_UV uv REQUIRED)
set(I2S_PYTHON "${I2S_UV}" run --locked --project "${PROJECT_SOURCE_DIR}")
add_test(NAME i2s_lint COMMAND ${I2S_PYTHON} python -m generator -d "${PROJECT_SOURCE_DIR}" --validate
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
add_test(NAME i2s_generator_check COMMAND ${I2S_PYTHON} python -m generator -d "${PROJECT_SOURCE_DIR}" --check
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
add_test(NAME i2s_pytest COMMAND ${I2S_PYTHON} pytest WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
add_test(NAME i2s_mypy COMMAND ${I2S_PYTHON} mypy WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")

# RTM Document_02
# Each broken narrative must fail the render with the guard's own message:
# Asciidoctor by itself exits 0 on all three.
set(guard_printed_include "render_document\\[unprocessed-include\\]")
set(guard_missing_include "render_document\\[asciidoctor-failed\\]")
set(guard_unincluded_table "render_document\\[unincluded-file\\]")
foreach(narrative printed_include missing_include unincluded_table)
    add_test(NAME i2s_document_refuses_${narrative}
        COMMAND "${CMAKE_COMMAND}" -DROOT=${PROJECT_SOURCE_DIR} -DOUT=${CMAKE_CURRENT_BINARY_DIR}/doc_${narrative}
                -DNARRATIVE=${CMAKE_CURRENT_SOURCE_DIR}/document/${narrative}.adoc
                -P "${PROJECT_SOURCE_DIR}/cmake/render_document.cmake")
    set_tests_properties(i2s_document_refuses_${narrative} PROPERTIES
        PASS_REGULAR_EXPRESSION "${guard_${narrative}}")
endforeach()
add_test(NAME i2s_document COMMAND "${CMAKE_COMMAND}" --build "${CMAKE_BINARY_DIR}" --target i2s_document)

set_tests_properties(i2s_generator_check PROPERTIES DEPENDS i2s_lint)
set(i2s_tests i2s_pytest i2s_mypy i2s_keys_tests i2s_renamed_key_fails_to_compile i2s_attributes_tests
    i2s_compile_fail_text_to_date_time i2s_compile_fail_int_to_text i2s_compile_fail_int_to_boolean
    i2s_compile_fail_unknown_key i2s_compile_fail_flat_spelling i2s_readme_examples i2s_two_units
    i2s_missing_implementation_fails_to_link i2s_install)
set_tests_properties(${i2s_tests} PROPERTIES DEPENDS i2s_generator_check)
set_tests_properties(i2s_document_refuses_printed_include i2s_document_refuses_missing_include
    i2s_document_refuses_unincluded_table
    PROPERTIES DEPENDS "${i2s_tests}")
set_tests_properties(i2s_document PROPERTIES DEPENDS
    "i2s_document_refuses_printed_include;i2s_document_refuses_missing_include;i2s_document_refuses_unincluded_table")
