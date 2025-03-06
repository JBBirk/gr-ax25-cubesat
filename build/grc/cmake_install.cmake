# Install script for directory: /home/jbb2002/gr-hwu/grc

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

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/gnuradio/grc/blocks" TYPE FILE FILES
    "/home/jbb2002/gr-hwu/grc/hwu_ax25_procedures.block.yml"
    "/home/jbb2002/gr-hwu/grc/hwu_ax25_extract_frame.block.yml"
    "/home/jbb2002/gr-hwu/grc/hwu_debug_add_ax25_header.block.yml"
    "/home/jbb2002/gr-hwu/grc/hwu_nrzi_encode_packed.block.yml"
    "/home/jbb2002/gr-hwu/grc/hwu_nrzi_decode_packed.block.yml"
    "/home/jbb2002/gr-hwu/grc/hwu_usrp_burst_tagger.block.yml"
    "/home/jbb2002/gr-hwu/grc/hwu_usrp_burst_tx.block.yml"
    "/home/jbb2002/gr-hwu/grc/hwu_ax25_extract_frame_v2.block.yml"
    )
endif()

