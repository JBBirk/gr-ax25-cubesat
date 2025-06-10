find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_HWU gnuradio-hwu)

FIND_PATH(
    GR_HWU_INCLUDE_DIRS
    NAMES gnuradio/hwu/api.h
    HINTS $ENV{HWU_DIR}/include
        ${PC_HWU_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_HWU_LIBRARIES
    NAMES gnuradio-hwu
    HINTS $ENV{HWU_DIR}/lib
        ${PC_HWU_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-hwuTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_HWU DEFAULT_MSG GR_HWU_LIBRARIES GR_HWU_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_HWU_LIBRARIES GR_HWU_INCLUDE_DIRS)
