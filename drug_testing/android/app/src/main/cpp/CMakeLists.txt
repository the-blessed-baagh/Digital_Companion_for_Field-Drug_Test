cmake_minimum_required(VERSION 3.22.1)
project(field_drug_testing_ffi)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(PROJECT_ROOT "${CMAKE_SOURCE_DIR}/../../../../..")
set(NATIVE_ROOT "${PROJECT_ROOT}/native")
set(CV_ENGINE_CPP "${PROJECT_ROOT}/cv_engine/cpp")

# ========== OpenCV 4.10 path ==========
set(OpenCV_DIR "C:/OpenCV-android-sdk/sdk/native/jni")
find_package(OpenCV REQUIRED)

add_library(field_drug_testing_ffi SHARED
        ${NATIVE_ROOT}/src/ffi_bridge.cpp
        ${CV_ENGINE_CPP}/src/drug_testing_pipeline.cpp
)

target_include_directories(field_drug_testing_ffi PRIVATE
        ${NATIVE_ROOT}/include
        ${CV_ENGINE_CPP}/include
        ${OpenCV_INCLUDE_DIRS}
)

find_library(log-lib log)

# OpenCV 4.x — simple linking works
target_link_libraries(field_drug_testing_ffi
        ${OpenCV_LIBS}
        ${log-lib}
)