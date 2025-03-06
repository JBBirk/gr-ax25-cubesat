#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
import pmt
from gnuradio import gr
import uhd
import time

class usrp_burst_tagger(gr.sync_block):
    """
    docstring for block usrp_burst_tagger
    """
    def __init__(self, usrp_sink):
        gr.sync_block.__init__(self,
            name="usrp_burst_tagger",
            in_sig=[np.complex64],
            out_sig=[np.complex64])
        self.offset = 0
        self.usrp = usrp_sink
        uhd.usrp

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        packet_len = 0
        # <+signal processing here+>

        tags = self.get_tags_in_window(0,0,len(in0))
        if tags:
            for tag in tags:
                if tag.key == pmt.intern("packet_len"):
                    packet_len = pmt.to_python(tag.value)
            send_time = self.usrp.get_time_now().get_real_secs() + 1 #For testing purposes, offset send time by 1 second

            tx_time_pmt = pmt.make_tuple(
                    pmt.from_long(int(send_time)),
                    pmt.from_double(send_time - int(send_time))
                )
            self.add_item_tag(0, self.offset, pmt.intern("tx_time"), tx_time_pmt)
            self.offset += packet_len

        out[:] = in0
        return len(output_items[0])
