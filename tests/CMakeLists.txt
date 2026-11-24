include(FetchContent)
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
include("${catch2_SOURCE_DIR}/extras/Catch.cmake")
catch_discover_tests(i2s_keys_tests)

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
