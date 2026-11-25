# RTM SingleHeader_03
# A program built against an installed I2S, as a consumer builds one: it finds
# the package by its CMake config in the install prefix and sees nothing of the
# source tree. cmake/install_test.cmake configures, builds and runs it.
cmake_minimum_required(VERSION 3.25)
project(I2SInstallConsumer LANGUAGES CXX)

find_package(I2S 0.1 REQUIRED CONFIG)

add_executable(i2s_install_consumer consumer.cpp)
target_link_libraries(i2s_install_consumer PRIVATE I2S::i2s)
target_compile_options(i2s_install_consumer PRIVATE
    $<IF:$<CXX_COMPILER_ID:MSVC>,/W4 /WX,-Wall -Wextra -Wpedantic -Werror>)
