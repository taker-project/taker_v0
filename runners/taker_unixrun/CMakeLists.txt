cmake_minimum_required(VERSION 3.0.2)
project(taker_unixrun)

set(CMAKE_CXX_STANDARD 14)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${PROJECT_SOURCE_DIR}/../../cmake/)

find_package(JsonCpp 1 EXACT REQUIRED)

add_executable(taker_unixrun main.cpp processrunner.cpp utils.cpp)
target_link_libraries(taker_unixrun JsonCpp::JsonCpp)

install(TARGETS taker_unixrun RUNTIME DESTINATION bin)
