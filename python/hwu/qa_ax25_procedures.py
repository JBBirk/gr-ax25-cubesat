#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

from gnuradio import gr, gr_unittest
# from gnuradio import blocks
from gnuradio.hwu import ax25_procedures

class qa_ax25_procedures(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_instance(self):
        # FIXME: Test will fail until you pass sensible arguments to the constructor
        instance = ax25_procedures(src_addr='HWUGND', dest_addr='HWUGND', rej="REJ")

    def test_001_frame_gen(self):
        # set up fg

        procedures = ax25_procedures(src_addr='HWUGND', dest_addr='HWUGND', rej="REJ")

        self.tb.run()
        # check data


if __name__ == '__main__':
    gr_unittest.run(qa_ax25_procedures)
