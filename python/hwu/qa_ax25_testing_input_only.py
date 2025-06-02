#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

from gnuradio import gr, gr_unittest, blocks, pdu
from gnuradio.hwu import ax25_testing_input_only

class qa_ax25_testing_input_only(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_instance(self):
        # FIXME: Test will fail until you pass sensible arguments to the constructor
        instance = ax25_testing_input_only('HWUGND', 1, 'HWUSAT', 1, True, 'REJ', 8, 2048, 7, 3, 10)

    def test_001_generate_frame(self):

        #define data

        data_in = [1,2,3]
        #define blocks
        src = blocks.vector_source_b(data_in, False, 1, [])
        to_tagged = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, 3, "tx_pck_len")
        to_pdu = pdu.tagged_stream_to_pdu(gr.types.byte_t, "tx_pck_len")
        ax25_impl = ax25_testing_input_only('HWUGND', 1, 'HWUSAT', 1, True, 'REJ', 8, 2048, 7, 3, 10)
        sink = blocks.message_debug()

        #set up connections
        self.tb.connect(src, to_tagged)
        self.tb.connect(to_tagged, to_pdu)
        self.tb.msg_connect(to_pdu, 'pdus', ax25_impl, 'Payload in')
        self.tb.msg_connect(ax25_impl, 'Frame out', sink, 'store')

        # set up fg
        self.tb.run()

        # check data
        print(sink.get_message(0))


if __name__ == '__main__':
    gr_unittest.run(qa_ax25_testing_input_only)
