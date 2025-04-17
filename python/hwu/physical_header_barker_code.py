#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


# import numpy
import pmt
from gnuradio import gr

class physical_header_barker_code(gr.basic_block):
    """
    Adds phycial layer header and optional tail containing barker codes.
    These help with synchronisation of the timing recovery and enhance sync performance
    """

    BARKER_CODES = {2: [2],   #[1,0],
                    3: [6],   #[1,1,0],
                    4: [13],  #[1,1,0,1],
                    5: [29],  #[1,1,1,0,1],
                    7: [114], #[1,1,1,0,0,1,0],
                    11: [7,18], #[1,1,1,0,0,0,1,0,0,1,0],
                    13: [31,53]#[1,1,1,1,1,0,0,1,1,0,1,0,1]
                    }
    
    def __init__(self, barker_len, add_tail):
        gr.basic_block.__init__(self,
            name="physical_header_barker_code",
            in_sig=[],
            out_sig=[])
        

        self.barker_sequence = self.BARKER_CODES[barker_len]
        self.add_tail = add_tail
        self.message_port_register_in(pmt.intern('Frame in'))
        self.set_msg_handler(pmt.intern('Frame in'), self.handle_frame_in)
        self.message_port_register_out(pmt.intern('Frame out'))

    
    def handle_frame_in(self, msg_pmt):

        data = self.barker_sequence
        data.extend(pmt.u8vector_elements(pmt.cdr(msg_pmt)))
        if self.add_tail:
            data.extend(self.barker_sequence)

        self.message_port_pub(pmt.intern('Frame out'), pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(data),data))) ## Overwrites Metadata
        data = []

        return


    # def work(self, input_items, output_items):
    #     in0 = input_items[0]
    #     out = output_items[0]
    #     # <+signal processing here+>
    #     out[:] = in0
    #     return len(output_items[0])
