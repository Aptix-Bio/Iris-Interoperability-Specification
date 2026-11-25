# RTM Readme_01
# Writes every ```cpp block of README.md into one C++ source, each block in its
# own function, so the README's examples compile as a test and cannot drift
# from the library. A block runs in its own scope with an `attributes` in
# reach, so an example may declare its own or use the one before it.
#
# The fence is the rule (decided 2026-11-25): ```cpp marks an example that
# needs only I2S and is compiled here; ```c++ marks one that needs a library
# I2S does not build against (a DICOM toolkit, IFE's Builder) and is skipped,
# since its headers are not available to this build.
#
#   cmake -DREADME=<README.md> -DOUT=<file.cpp> -P cmake/readme_examples.cmake
cmake_minimum_required(VERSION 3.25)
file(READ "${README}" text)
# A CMake list is ;-separated, so every ; in the C++ is held as a placeholder
# while the blocks are a list, and restored when each is written.
string(REPLACE ";" "@I2S_SEMICOLON@" text "${text}")
string(REGEX MATCHALL "```cpp\n[^`]*```" blocks "${text}")
list(LENGTH blocks count)
if(count EQUAL 0)
    message(FATAL_ERROR "readme_examples: ${README} has no ```cpp block")
endif()
set(source "// Generated from ${README} by cmake/readme_examples.cmake. DO NOT EDIT BY HAND.\n")
# The examples are a program's one translation unit, so it defines
# I2S_IMPLEMENTATION before including the one header, as the README tells a
# consumer to.
string(APPEND source "#define I2S_IMPLEMENTATION\n#include \"I2S.hpp\"\n\n#include <chrono>\n#include <iostream>\n\n")
set(index 0)
set(calls "")
foreach(block IN LISTS blocks)
    string(REGEX REPLACE "^```cpp\n" "" body "${block}")
    string(REGEX REPLACE "```$" "" body "${body}")
    string(REPLACE "@I2S_SEMICOLON@" ";" body "${body}")
    string(APPEND source "static void readme_example_${index}([[maybe_unused]] I2S::Attributes& attributes)\n{\n{\n${body}}\n}\n\n")
    string(APPEND calls "    readme_example_${index}(attributes);\n")
    math(EXPR index "${index} + 1")
endforeach()
string(APPEND source "int main()\n{\n    I2S::Attributes attributes;\n    attributes[I2S::Attribute::Manufacturer] = \"Leica\";\n${calls}    return 0;\n}\n")
file(WRITE "${OUT}" "${source}")
