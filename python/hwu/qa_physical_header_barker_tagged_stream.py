#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

from gnuradio import gr, gr_unittest
from gnuradio import blocks, pdu
try:
    from gnuradio.hwu import physical_header_barker_tagged_stream
except ImportError:
    import os
    import sys
    dirname, filename = os.path.split(os.path.abspath(__file__))
    sys.path.append(os.path.join(dirname, "bindings"))
    from gnuradio.hwu import physical_header_barker_tagged_stream

class qa_physical_header_barker_tagged_stream(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_instance(self):
        # FIXME: Test will fail until you pass sensible arguments to the constructor
        instance = physical_header_barker_tagged_stream(11, False, "tx_packet_len")

    def test_001_Physical_header_barker_tagged_stream(self):

        # define blocks
        data_in = (1,2,3)
        expected_result = (7,18,1,2,3)
        src=blocks.vector_source_b(data_in, False, 1, [])
        to_tagged = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, 3, "tx_packet_len")
        add_header=physical_header_barker_tagged_stream(11, False, "tx_packet_len")
        sink=blocks.vector_sink_b(1,1024)

        # set up connections
        self.tb.connect(src, to_tagged, add_header, sink)

        # set up fg
        self.tb.run()

        # check data
        results = sink.data()
        self.assertEqual(results, expected_result)





if __name__ == '__main__':
    gr_unittest.run(qa_physical_header_barker_tagged_stream)
