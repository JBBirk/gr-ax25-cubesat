#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr
import pmt

class debug_add_ax25_header(gr.basic_block):
    """
    docstring for block debug_add_ax25_header
    """
    def __init__(self):
        gr.basic_block.__init__(self,
            name="debug_add_ax25_header",
            in_sig=[],
            out_sig=[])
        
        self.message_port_register_in(pmt.intern('in'))
        self.message_port_register_out(pmt.intern('out'))
        self.set_msg_handler(pmt.intern('in'), self.handle_in)

    def handle_in(self):
        

