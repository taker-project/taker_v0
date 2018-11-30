cmake_minimum_required(VERSION 2.6)
project(tests)

set(CMAKE_CXX_STANDARD 14)
add_compile_options(-Wall -Wextra -pedantic -Weffc++ -Werror)


add_executable(basic_test basic_test.cpp)
