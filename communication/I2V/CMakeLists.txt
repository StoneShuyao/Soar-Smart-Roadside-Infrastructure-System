# ================================================================================ #
# project macros
# ================================================================================ #
cmake_minimum_required(VERSION 3.8)
project(libroad CXX C)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CMAKE_CURRENT_SOURCE_DIR}/cmake)

set(CMAKE_BUILD_TYPE Release)
set(CMAKE_CXX_FLAGS_RELEASE "-O3")

# ================================================================================ #
# 3rd party libraries
# ================================================================================ #
find_package(PCAP REQUIRED)
include_directories(${PROJECT_SOURCE_DIR}/include/)

file(GLOB LIBROAD_SOURCE src/*.cpp)
file(GLOB LIBROAD_HEADER include/*.h)

add_library(v2x_socket SHARED ${LIBROAD_SOURCE} ${LIBROAD_HEADER})
target_include_directories(v2x_socket PUBLIC include ${PCAP_INCLUDE_DIR})
target_link_libraries(v2x_socket PRIVATE ${PCAP_LIBRARY})

# livox related
add_subdirectory(livox_sdk livox_sdk)

add_executable(libroad_tx libroad_tx.cpp)
target_link_libraries(libroad_tx PRIVATE v2x_socket pthread livox_sdk)
add_executable(libroad_rx libroad_rx.cpp)
target_link_libraries(libroad_rx PRIVATE v2x_socket)
add_executable(libroad_tx_demo libroad_tx_demo.cpp)
target_link_libraries(libroad_tx_demo PRIVATE v2x_socket pthread livox_sdk)

install(TARGETS v2x_socket DESTINATION lib)
install(FILES include/v2x_socket.h DESTINATION include)
