cmake_minimum_required(VERSION 3.22)
project(hello_cpp LANGUAGES CXX)

# ROS 2 Jazzy binaries use libstdc++ and C++17; the cppsrc libc++/C++26 settings do not apply here.
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(talker src/talker.cpp)
target_compile_options(talker PRIVATE -Wall -Wextra -Wpedantic)
target_link_libraries(talker PRIVATE rclcpp::rclcpp ${std_msgs_TARGETS})

install(TARGETS talker DESTINATION lib/${PROJECT_NAME})

ament_package()
