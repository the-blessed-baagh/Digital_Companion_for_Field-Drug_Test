cmake_minimum_required(VERSION 3.22.1)
project(field_drug_testing_ffi LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Path to the original CV engine sources (relative to this CMakeLists)
set(CV_ENGINE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../cv_engine/cpp")

# OpenCV – on Android this is normally provided via OpenCV Android SDK
# For local desktop testing you can still point OpenCV_DIR
find_package(OpenCV REQUIRED)

add_library(field_drug_testing_ffi SHARED
    src/ffi_bridge.cpp
    ${CV_ENGINE_ROOT}/src/drug_testing_pipeline.cpp
)

target_include_directories(field_drug_testing_ffi PRIVATE
    include
    ${CV_ENGINE_ROOT}/include
    ${OpenCV_INCLUDE_DIRS}
)

target_link_libraries(field_drug_testing_ffi PRIVATE
    ${OpenCV_LIBS}
)

# On Android also link log
if(ANDROID)
    find_library(log-lib log)
    target_link_libraries(field_drug_testing_ffi PRIVATE ${log-lib})
endif()

message(STATUS "Building field_drug_testing_ffi shared library")
message(STATUS "OpenCV version: ${OpenCV_VERSION}")
