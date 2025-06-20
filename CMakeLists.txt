cmake_minimum_required(VERSION 3.12)
project(motor_sjoin_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Encontrar Python y Pybind11
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
find_package(pybind11 REQUIRED)

# Encontrar GEOS usando la herramienta pkg-config
find_package(PkgConfig REQUIRED)
pkg_check_modules(GEOS REQUIRED geos)

# Crear el módulo de Python
pybind11_add_module(motor_sjoin_cpp bindings.cpp procesador_sjoin.cpp)

# Configurar las banderas de compilación para alto rendimiento y paralelismo
target_compile_options(motor_sjoin_cpp PRIVATE -O3 -fPIC -Wall -fopenmp)

# Enlazar las librerías necesarias
target_include_directories(motor_sjoin_cpp PRIVATE ${GEOS_INCLUDE_DIRS})
target_link_libraries(motor_sjoin_cpp PRIVATE ${GEOS_LIBRARIES})
