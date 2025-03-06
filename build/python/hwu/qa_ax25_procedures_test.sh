#!/usr/bin/sh
export VOLK_GENERIC=1
export GR_DONT_LOAD_PREFS=1
export srcdir=/home/jbb2002/gr-hwu/python/hwu
export GR_CONF_CONTROLPORT_ON=False
export PATH="/home/jbb2002/gr-hwu/build/python/hwu":"$PATH"
export LD_LIBRARY_PATH="":$LD_LIBRARY_PATH
export PYTHONPATH=/home/jbb2002/gr-hwu/build/test_modules:$PYTHONPATH
/usr/bin/python3 /home/jbb2002/gr-hwu/python/hwu/qa_ax25_procedures.py 
