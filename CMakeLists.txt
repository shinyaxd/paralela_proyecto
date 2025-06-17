cmake_minimum_required(VERSION 3.10)
project(motor_sjoin_cpp)

set(CMAKE_CXX_STANDARD 17)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
find_package(pybind11 REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(GEOS REQUIRED geos)

include_directories(${GEOS_INCLUDE_DIRS})
link_directories(${GEOS_LIBRARY_DIRS})

add_compile_options(-O3 -fopenmp -march=native -fPIC)

pybind11_add_module(motor_sjoin_cpp bindings.cpp procesador_sjoin.cpp)
target_link_libraries(motor_sjoin_cpp PRIVATE ${GEOS_LIBRARIES} OpenMP::OpenMP_CXX)
