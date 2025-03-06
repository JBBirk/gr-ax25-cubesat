# Install script for directory: /home/jbb2002/gr-hwu/python/hwu

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/jbb2002/.local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Debug")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/home/jbb2002/gr-hwu/build/python/hwu/bindings/cmake_install.cmake")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3.8/site-packages/gnuradio/hwu" TYPE FILE FILES
    "/home/jbb2002/gr-hwu/python/hwu/__init__.py"
    "/home/jbb2002/gr-hwu/python/hwu/ax25_constants.py"
    "/home/jbb2002/gr-hwu/python/hwu/ax25_connectors.py"
    "/home/jbb2002/gr-hwu/python/hwu/ax25_framer.py"
    "/home/jbb2002/gr-hwu/python/hwu/ax25_transceiver.py"
    "/home/jbb2002/gr-hwu/python/hwu/ax25_procedures.py"
    "/home/jbb2002/gr-hwu/python/hwu/ax25_extract_frame.py"
    "/home/jbb2002/gr-hwu/python/hwu/nrzi_encode_packed.py"
    "/home/jbb2002/gr-hwu/python/hwu/nrzi_decode_packed.py"
    "/home/jbb2002/gr-hwu/python/hwu/usrp_burst_tagger.py"
    "/home/jbb2002/gr-hwu/python/hwu/ax25_extract_frame_v2.py"
    )
endif()

