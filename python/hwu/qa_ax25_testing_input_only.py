#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
import time
import pmt
from gnuradio import gr, gr_unittest, blocks, pdu
from gnuradio.hwu import ax25_testing_input_only

class qa_ax25_testing_input_only(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_instance(self):
        instance = ax25_testing_input_only('HWUGND', 1, 'HWUSAT', 1, True, 'REJ', 8, 2048, 7, 3, 10)

    def test_001_generate_frame(self):

        #define data

        data_in = [1,2,3]
        #               Sync,   HWUSAT,                              SSID=1, HWUGND,                         SSID=1, C-Field, PID, 1 (0 inserted),   2,   3,  crc,      Sync (shifted)
        expected_frame = [0x7e, 0x12, 0xea, 0xaa, 0xca, 0x82, 0x2a, 0x47, 0x12, 0xea, 0xaa, 0xe2, 0x72, 0x22, 0xc6,   0x00,   0x0f, 0x80,         0x20, 0x60, 0x7d, 0xf4, 0xcf, 0xc0]

        ##################################################
        # Blocks
        ##################################################
        hwu_ax25_testing_input_only_0 = ax25_testing_input_only('HWUGND', 1, 'HWUSAT', 1, True, 'REJ', 8, 2048, 7, 3, 10)
        blocks_message_strobe_0 = blocks.message_strobe(pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(3,data_in) ), 1000)
        message_sink = blocks.message_debug(True)


        ##################################################
        # Connections
        ##################################################
        self.tb.msg_connect((blocks_message_strobe_0, 'strobe'), (hwu_ax25_testing_input_only_0, 'Payload in'))
        self.tb.msg_connect((hwu_ax25_testing_input_only_0, 'Frame out'), (message_sink, 'store'))

        # set up fg
        self.tb.start()
        deadline = time.time() + 5.0
        while time.time() < deadline:
            if message_sink.num_messages() > 0:
                break
            time.sleep(0.05)
        self.tb.stop()
        self.tb.wait()
        assert message_sink.num_messages() > 0

        # check data
        msg = pmt.u8vector_elements(pmt.cdr(message_sink.get_message(0)))

        assert len(msg) == len(expected_frame)
        assert msg == expected_frame


if __name__ == '__main__':
    gr_unittest.run(qa_ax25_testing_input_only)
