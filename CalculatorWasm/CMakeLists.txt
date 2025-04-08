cmake_minimum_required(VERSION 3.30)
project(CalculatorWasm)

set(CMAKE_CXX_STANDARD 14)

include_directories(CPPVersion)

add_executable(CalculatorWasm
    CPPVersion/calculator.cpp)
