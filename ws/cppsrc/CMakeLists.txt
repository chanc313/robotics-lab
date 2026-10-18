cmake_minimum_required(VERSION 3.24)
project(robotics_lab LANGUAGES CXX)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")

# CMake 3.28 maps CXX_STANDARD 26 only for Clang >= 17, so pass the flag directly
# and accept any compiler that understands -std=c++2c.
include(CheckCXXCompilerFlag)
check_cxx_compiler_flag("-std=c++2c" ROBOTICS_LAB_HAS_CPP26)
if(NOT ROBOTICS_LAB_HAS_CPP26)
    message(FATAL_ERROR "C++26 requires a compiler supporting -std=c++2c. Set CXX before configuring.")
endif()

add_executable(main main.cpp)
target_include_directories(main PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include")
target_compile_options(main PRIVATE -std=c++2c -Wall -Wextra -Wpedantic)
# libc++ stays local to this sandbox target; ROS packages link the system libstdc++.
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    target_compile_options(main PRIVATE -stdlib=libc++)
    target_link_options(main PRIVATE -stdlib=libc++)
endif()
