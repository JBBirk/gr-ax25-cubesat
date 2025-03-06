# CMake generated Testfile for 
# Source directory: /home/jbb2002/gr-hwu/python/hwu
# Build directory: /home/jbb2002/gr-hwu/build/python/hwu
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(qa_ax25_extract_frame "/usr/bin/sh" "qa_ax25_extract_frame_test.sh")
set_tests_properties(qa_ax25_extract_frame PROPERTIES  _BACKTRACE_TRIPLES "/home/jbb2002/.local/lib/cmake/gnuradio/GrTest.cmake;119;add_test;/home/jbb2002/gr-hwu/python/hwu/CMakeLists.txt;50;GR_ADD_TEST;/home/jbb2002/gr-hwu/python/hwu/CMakeLists.txt;0;")
subdirs("bindings")
