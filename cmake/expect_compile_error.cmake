# RTM TypedKeys_01
# Passes when building TARGET fails and the compiler's output contains every
# string in EXPECT (a ;-list): the build must fail for the stated reason, not
# for any reason.
#
#   cmake -DBINARY_DIR=<build> -DTARGET=<target> -DEXPECT=<a;b> -P cmake/expect_compile_error.cmake
cmake_minimum_required(VERSION 3.25)
execute_process(
    COMMAND "${CMAKE_COMMAND}" --build "${BINARY_DIR}" --target "${TARGET}"
    RESULT_VARIABLE result
    OUTPUT_VARIABLE output
    ERROR_VARIABLE output)
if(result EQUAL 0)
    message(FATAL_ERROR "expect_compile_error: ${TARGET} compiled, and it must not")
endif()
foreach(expected IN LISTS EXPECT)
    string(FIND "${output}" "${expected}" found)
    if(found EQUAL -1)
        message("${output}")
        message(FATAL_ERROR "expect_compile_error: ${TARGET} failed, but its output does not name '${expected}'")
    endif()
endforeach()
message(STATUS "expect_compile_error: ${TARGET} failed as expected, naming: ${EXPECT}")
