#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 Julian Birk.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
import numpy as np
import pmt
import random
import bitstring as bs
from gnuradio import gr, gr_unittest
from gnuradio import blocks
from ax25_extract_frame_v2 import ax25_extract_frame_v2 as frame_extractor

class qa_ax25_extract_frame(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_ax25_frame_extraction(self):
        # Define the AX.25 sync word byte
        sync_byte = 0x7e

        # Create a sample input with two frames, delimited by 0x7e bytes
        # Frame 1: [0x01, 0x02, 0x03]
        # Frame 2: [0xAA, 0xBB, 0xCC]
        input_bytes = [0x01,
            sync_byte, 0x01, 0x02, 0x03, sync_byte,
            sync_byte, 0xAA, 0xBB, 0xCC, sync_byte
        ]

        # Expected output frames as numpy arrays (each frame excluding the sync words)
        expected_frames = [
            np.array([0x01], dtype=np.uint8),
            np.array([0x01, 0x02, 0x03], dtype=np.uint8),
            np.array([], dtype=np.uint8),
            np.array([0xAA, 0xBB, 0xCC], dtype=np.uint8)
        ]

        # Set up the blocks for the test
        src = blocks.vector_source_b(input_bytes, repeat=False)
        ax25_extractor = frame_extractor()
        sink = blocks.message_debug()

        # Connect blocks
        self.tb.connect(src, ax25_extractor)
        self.tb.msg_connect(ax25_extractor, 'Frame out', sink, "store")

        # Run the flowgraph
        self.tb.run()

        num_messages = sink.num_messages()
        self.assertEqual(num_messages, len(expected_frames), "Incorrect number of frames detected.")


        # Check the output PDUs
        for i, expected_frame in enumerate(expected_frames):
            # Retrieve the message from the sink
            msg = sink.get_message(i)
            if msg is None:
                self.fail(f"Expected frame {i+1} not found in the output.")

            # Extract the frame data from the PDU message
            pdu_data = pmt.cdr(msg)  # pmt.cdr extracts the payload
            frame = np.array(pmt.u8vector_elements(pdu_data), dtype=np.uint8)
            print("Actual frame: ", frame, " expected frame: ", expected_frame)

            # Assert that the frame matches the expected frame
            np.testing.assert_array_equal(frame, expected_frame, err_msg=f"Frame {i+1} did not match expected output.")

    def test_split_sync_word(self):
        # # Test where sync word 0x7e is split across two bytes in the stream
        # input_bytes = [
        #     0x3f, 0xbf,   # These bits together form a split 0x7e
        #     0x01, 0x02, 0x03,
        #     0x7e          # Proper 0x7e ending
        # ]
        input_bytes = [ #equivalent to one added 0-bit at the beginning and 7 added bits at the end # Change: Added one more byte in the beginning to observe behaviour
            0x11,
            0x3f, 0x66, 0x2A, 0xbf, 0x0f
        ]

        expected_frames = [
            np.array([0x11], dtype=np.uint8),
            np.array([0xcc, 0x55], dtype=np.uint8)
        ]
        # # Expected frame when the sync word is split across bytes
        # expected_frames = [
        #     np.array([0x01, 0x02, 0x03], dtype=np.uint8)
        # ]

        # Set up the blocks for the test
        src = blocks.vector_source_b(input_bytes, repeat=False)
        ax25_extractor = frame_extractor()
        sink = blocks.message_debug()

        # Connect blocks
        self.tb.connect(src, ax25_extractor)
        self.tb.msg_connect(ax25_extractor, 'Frame out', sink, "store")

        # Run the flowgraph
        self.tb.run()

        num_messages = sink.num_messages()
        self.assertEqual(num_messages, len(expected_frames), "Incorrect number of frames detected.")


        # Check the output PDUs
        for i, expected_frame in enumerate(expected_frames):
            # Retrieve the message from the sink
            msg = sink.get_message(i)
            if msg is None:
                self.fail(f"Expected frame {i+1} not found in the output.")

            # Extract the frame data from the PDU message
            pdu_data = pmt.cdr(msg)  # pmt.cdr extracts the payload
            frame = np.array(pmt.u8vector_elements(pdu_data), dtype=np.uint8)
            print("Actual frame: ", frame, " expected frame: ", expected_frame)

            # Assert that the frame matches the expected frame
            np.testing.assert_array_equal(frame, expected_frame, err_msg=f"Frame {i+1} did not match expected output.")

    def test_against_bitstring_rand(self):
        # Define the AX.25 sync word byte
            sync_byte = 0x7e  

        # for i in range(1):
            
            # if i == 0:
            #     stuffed_frame = bs.BitArray(hex='0x7e485755474e44e24857555341546300f0deadbeef0000001f0000000200000d060002006748957c0007100c0000000000000000000000018c3a62f7bbe07e')
            #     data = [byte for byte in stuffed_frame.tobytes()]
            #     data = np.array(data, dtype=np.uint8)
            # else:
            data = [random.randint(0,255) for _ in range(random.randint(200,500))]
            data.insert(0, sync_byte)
            data.append(sync_byte)

            stuffed_frame = bs.BitArray(bytes=bytes(data))
            stuffed_frame.replace('0b11111', '0b111110', 8, -8)

            inputframe = [byte for byte in stuffed_frame.tobytes()]

            unstuffed_frame = stuffed_frame
            unstuffed_frame.replace('0b111110', '0b11111', 8, -8)
            
            expected_decoded_data = [byte for byte in unstuffed_frame.tobytes()]
            expected_decoded_data = np.array(expected_decoded_data[1:-1], dtype=np.uint8)

            src = blocks.vector_source_b(inputframe, repeat=False)
            ax25_extractor = frame_extractor()
            sink = blocks.message_debug()
            self.tb.connect(src, ax25_extractor)
            self.tb.msg_connect(ax25_extractor, 'Frame out', sink, "store")

            # Run the flowgraph
            self.tb.run()

            num_messages = sink.num_messages()
            self.assertEqual(num_messages, 2, "Incorrect number of frames detected.")

            msg = sink.get_message(1)
            if msg is None:
                self.fail("Expected frame not found in the output.")

            # Extract the frame data from the PDU message
            pdu_data = pmt.cdr(msg)
            frame = np.array(pmt.u8vector_elements(pdu_data), dtype=np.uint8)
            # hex_frame = [hex(num) for num in frame]
            # print(hex_frame)

            np.testing.assert_array_equal(frame, expected_decoded_data, err_msg=f"Error found between input: {data} \n bitstring: {expected_decoded_data} \n and actual frame: {frame}")

    # def test_bitstuffing(self):
    #     # Define the AX.25 sync word byte
    #     sync_byte = 0x7e

    #     # Create a sample input with two frames, delimited by 0x7e bytes
    #     # Frame 1: [0x01, 0x02, 0x03]
    #     # Frame 2: [0xAA, 0xBB, 0xCC]
    #     input_bytes = [
    #         sync_byte, 0b11111010, 0b11111010, 0b10000000, 0b01011111, 0b10000000
    #     ]

    #     # Expected output frames as numpy arrays (each frame excluding the sync words)
    #     expected_frames = [
    #         np.array([0xfd, 0xfa, 0x01], dtype=np.uint8)
    #     ]

    #     # Set up the blocks for the test
    #     src = blocks.vector_source_b(input_bytes, repeat=False)
    #     ax25_extractor = frame_extractor()
    #     sink = blocks.message_debug()

    #     # Connect blocks
    #     self.tb.connect(src, ax25_extractor)
    #     self.tb.msg_connect(ax25_extractor, 'Frame out', sink, "store")

    #     # Run the flowgraph
    #     self.tb.run()

    #     num_messages = sink.num_messages()
    #     self.assertEqual(num_messages, len(expected_frames), "Incorrect number of frames detected.")


    #     # Check the output PDU
    #     msg = sink.get_message(0)
    #     if msg is None:
    #         self.fail("Expected frame not found in the output.")

    #     # Extract the frame data from the PDU message
    #     pdu_data = pmt.cdr(msg)
    #     frame = np.array(pmt.u8vector_elements(pdu_data), dtype=np.uint8)

    #     # Assert that the frame matches the expected frame
    #     np.testing.assert_array_equal(frame, expected_frames[0], err_msg="Frame did not match expected output for split sync word test.")


# Run the test
if __name__ == '__main__':
    gr_unittest.run(qa_ax25_extract_frame)
    # test = qa_ax25_extract_frame()
    # test.setUp()
    # test.test_ax25_frame_extraction()
# import numpy as np
# from gnuradio import gr, gr_unittest
# from gnuradio import blocks
# from ax25_extract_frame_v2 import ax25_extract_frame_v2 as frame_extractor