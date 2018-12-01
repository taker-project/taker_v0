cmake_minimum_required(VERSION 2.6)
project(tests)

set(CMAKE_CXX_STANDARD 14)
add_compile_options(-Wall -Wextra -pedantic -Weffc++ -Werror)

add_executable(cut_exe cut_exe.cpp)

add_executable(basic_test basic_test.cpp)
add_executable(sleepy_test sleepy_test.cpp)
add_executable(worky_test worky_test.cpp)
add_executable(memory_test memory_test.cpp)
add_executable(vector_test vector_test.cpp)
add_executable(vector_pushback_test vector_pushback_test.cpp)
add_executable(alloc1_test alloc1_test.cpp)
add_executable(alloc2_test alloc2_test.cpp)
add_executable(env_test env_test.cpp)
add_executable(runerror_test runerror_test.cpp)
add_executable(args_test args_test.cpp)

add_custom_command(
    COMMAND "cut_exe${CMAKE_EXECUTABLE_SUFFIX}"
            "basic_test${CMAKE_EXECUTABLE_SUFFIX}"
            "broken_test${CMAKE_EXECUTABLE_SUFFIX}"
    OUTPUT "broken_test${CMAKE_EXECUTABLE_SUFFIX}"
    DEPENDS basic_test cut_exe
)

add_custom_target(more_tests DEPENDS "broken_test${CMAKE_EXECUTABLE_SUFFIX}")
