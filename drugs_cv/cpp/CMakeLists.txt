cmake_minimum_required(VERSION 3.20)
project(KAVACH_CV_CPP LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Check default OpenCV download location if not specified
if(NOT DEFINED OpenCV_DIR AND EXISTS "C:/Users/User/Downloads/opencv/build")
    set(OpenCV_DIR "C:/Users/User/Downloads/opencv/build")
    message(STATUS "Using downloaded OpenCV from: ${OpenCV_DIR}")
endif()

find_package(OpenCV REQUIRED)

include_directories(include ${OpenCV_INCLUDE_DIRS})

add_executable(kavach_cv
    src/main.cpp
    src/kavach_pipeline.cpp
    include/kavach_pipeline.hpp
    include/ciede2000.hpp
)

target_include_directories(kavach_cv PRIVATE
    include
    ${OpenCV_INCLUDE_DIRS}
)

target_link_libraries(kavach_cv PRIVATE
    ${OpenCV_LIBS}
)

message(STATUS "OpenCV library found: ${OpenCV_VERSION}")
message(STATUS "OpenCV include dirs: ${OpenCV_INCLUDE_DIRS}")
