#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr

class usrp_burst_tx(gr.sync_block):
    """
    docstring for block usrp_burst_tx
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name="usrp_burst_tx",
            in_sig=[],
            out_sig=None)


    def work(self, input_items, output_items):
        in0 = input_items[0]
        # <+signal processing here+>
        return len(input_items[0])
