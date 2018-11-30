cmake_minimum_required(VERSION 2.6)
project(tests)

set(CMAKE_CXX_STANDARD 14)
add_compile_options(-Wall -Wextra -pedantic -Weffc++ -Werror)


add_executable(basic_test basic_test.cpp)
add_executable(sleepy_test sleepy_test.cpp)
add_executable(worky_test worky_test.cpp)
add_executable(memory_test memory_test.cpp)
add_executable(vector_test vector_test.cpp)
add_executable(vector_pushback_test vector_pushback_test.cpp)
