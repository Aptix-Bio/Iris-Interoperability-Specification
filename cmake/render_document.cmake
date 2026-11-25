# RTM Document_02
# Renders the I2S specification to HTML and PDF:
#
#     NARRATIVE (spec/i2s_spec.adoc)     hand-written narrative
#   + GENERATED (generated_docs/*.adoc)  every table and key section, from spec/*.json
#   = OUT/i2s_spec.html and OUT/i2s_spec.pdf
#
#   cmake -DROOT=<repository> -DOUT=<dir> [-DNARRATIVE=<file>] [-DGENERATED=<dir>] -P cmake/render_document.cmake
#
# Asciidoctor and Asciidoctor PDF come from the repository's Gemfile.lock
# through `bundle exec`, so a local render and CI's use the same versions.
# Any warning fails the render (--failure-level=WARN), and so do the two
# failures Asciidoctor does not report: a missing include left as text in the
# output, and an include:: not at column 0, which is printed instead of
# processed. Each failure names its guard in brackets, one token the tests
# match. A generated file the narrative never includes fails too, since
# no reader would see it.
cmake_minimum_required(VERSION 3.25)
foreach(required ROOT OUT)
    if(NOT DEFINED ${required})
        message(FATAL_ERROR "render_document: -D${required}=<path> is required")
    endif()
endforeach()
if(NOT DEFINED NARRATIVE)
    set(NARRATIVE "${ROOT}/spec/i2s_spec.adoc")
endif()
if(NOT DEFINED GENERATED)
    set(GENERATED "${ROOT}/generated_docs")
endif()
find_program(BUNDLE bundle REQUIRED)
set(ENV{BUNDLE_GEMFILE} "${ROOT}/Gemfile")
file(MAKE_DIRECTORY "${OUT}")

file(STRINGS "${NARRATIVE}" included REGEX "^include::\\{generated\\}/[a-z_]+\\.adoc\\[\\]$")
file(GLOB generated_files RELATIVE "${GENERATED}" "${GENERATED}/*.adoc")
foreach(name IN LISTS generated_files)
    if(NOT "include::{generated}/${name}[]" IN_LIST included)
        message(FATAL_ERROR "render_document[unincluded-file]: ${NARRATIVE} never includes ${GENERATED}/${name} at column 0")
    endif()
endforeach()

foreach(format html pdf)
    set(command asciidoctor)
    if(format STREQUAL "pdf")
        set(command asciidoctor-pdf)
    endif()
    execute_process(
        COMMAND "${BUNDLE}" exec ${command} --failure-level=WARN -a "generated=${GENERATED}"
                -o "${OUT}/i2s_spec.${format}" "${NARRATIVE}"
        RESULT_VARIABLE result
    )
    if(NOT result EQUAL 0)
        message(FATAL_ERROR "render_document[asciidoctor-failed]: ${command} failed (exit ${result}) on ${NARRATIVE}")
    endif()
    file(SIZE "${OUT}/i2s_spec.${format}" size)
    if(size EQUAL 0)
        message(FATAL_ERROR "render_document: ${OUT}/i2s_spec.${format} is empty")
    endif()
endforeach()

file(READ "${OUT}/i2s_spec.html" html)
foreach(marker "Unresolved directive" "include::")
    string(FIND "${html}" "${marker}" found)
    if(NOT found EQUAL -1)
        message(FATAL_ERROR "render_document[unprocessed-include]: ${OUT}/i2s_spec.html contains '${marker}': an include was not processed")
    endif()
endforeach()
message(STATUS "render_document: ${OUT}/i2s_spec.html and ${OUT}/i2s_spec.pdf")
