cmake_minimum_required(VERSION 3.0.2)
project(taker_unixrun VERSION 0.1)

set(taker_unixrun_VERSION_NUMBER 1)

set(CMAKE_CXX_STANDARD 14)
add_compile_options(-Wall -Wextra -pedantic -Weffc++ -Werror)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${PROJECT_SOURCE_DIR}/../../../cmake/)

find_package(JsonCpp 1 EXACT REQUIRED)

include(CheckFunctionExists)
check_function_exists(pipe2 HAVE_PIPE2)

configure_file(${PROJECT_SOURCE_DIR}/config.hpp.in ${PROJECT_BINARY_DIR}/config.hpp)

add_executable(taker_unixrun main.cpp processrunner.cpp utils.cpp)
target_link_libraries(taker_unixrun JsonCpp::JsonCpp)
target_include_directories(taker_unixrun PUBLIC ${PROJECT_BINARY_DIR})

install(TARGETS taker_unixrun RUNTIME DESTINATION bin)
