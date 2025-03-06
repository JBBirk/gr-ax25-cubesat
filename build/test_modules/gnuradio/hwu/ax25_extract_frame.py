#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
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


import numpy
import pmt
from gnuradio import gr

class ax25_extract_frame(gr.sync_block):
    """
    docstring for block extract_frame
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name="extract_frame",
            in_sig=[numpy.uint8],
            out_sig=None)

        # Variables
        self.bit_buffer_input = []
        self.bit_buffer_output = []
        self.frame_buffer = []
        # self.bitcount = 0
        # self.currentbyte = 0
        self.active_frame = False
        self.ones = 0

        # Syncword constants:
        self.SYNC_WORD = [0,1,1,1,1,1,1,0]
        # self.BUGGY_ELONGATED_SYNC_WORD = [0,1,1,1,1,1,1,1,0]
        self.SYNC_LEN = len(self.SYNC_WORD)
        # self.BUGGY_SYN_LEN = len(self.BUGGY_ELONGATED_SYNC_WORD)



        self.message_port_register_out(pmt.intern('Frame out'))

    def work(self, input_items, output_items):
        in0 = input_items[0]

        for byte in in0:
            for i in range(8):  
                self.bit_buffer_input.append((byte >> (7-i)) & 0x1)

                if len(self.bit_buffer_input) < self.SYNC_LEN: #skip if less than 8 bits read
                    continue

                if self.active_frame:
                    if self.bit_buffer_input[-self.SYNC_LEN:] == self.SYNC_WORD and self.bit_buffer_output[:-self.SYNC_LEN+1]: #second sync word -> end of frame
                        
                        # build and send pdus 
                        # remove remnants of sync from ouput_buffer, as last 0 is never added
                        self.bit_buffer_output[:] = [bit for bit in self.bit_buffer_output[:-self.SYNC_LEN+1] if self.determine_bit_to_keep(bit)] #Undo bitstuffing

                        self.assemble_bytes()

                        # self.cleanup_framebuffer() #This seems to cause issues, if actual data is 0x7e
                        # Items inside the framebuffer are originale numpy.int64, which pmt doesn't like. So its converted to native pyhton int
                        self.frame_buffer = [int(item) for item in self.frame_buffer]

                        pdu = pmt.init_u8vector(len(self.frame_buffer), self.frame_buffer)
                        self.message_port_pub(pmt.intern('Frame out'), pmt.cons(pmt.PMT_NIL, pdu))

                        self.reset_state()

                    else: # in frame, fill bytes up
                        
                        self.bit_buffer_output.append(self.bit_buffer_input[-1])

                        # self.currentbyte = (self.currentbyte << 1) | self.bit_buffer[-1] if self.bitcount % 8 else self.bit_buffer[-1]
                        # self.bitcount += 1

                        # if self.bitcount == 8: #Assembled full byte, put into buffer and reset
                        #     self.frame_buffer.append(self.currentbyte)
                        #     self.bitcount = 0
                        #     self.currentbyte = 0

                elif self.bit_buffer_input[-self.SYNC_LEN:] == self.SYNC_WORD: #or self.bit_buffer_input[-self.BUGGY_SYN_LEN:] == self.BUGGY_ELONGATED_SYNC_WORD: #first syncword, beginning of frame
                    self.active_frame = True
                    self.frame_buffer = []
                
                
        return len(input_items[0])
    
    def determine_bit_to_keep(self, bit):
        
        if bit: # Keep track of consecutive ones
            self.ones += 1
            return True
        
        if 5 == self.ones: # Bit is 0 and we have 5 consecutive ones, the 0 was bitstuffed.
            self.ones = 0
            return False
        
        self.ones = 0 #If not, reset as just a regular 0 bit.
        return True
    
    def assemble_bytes(self):

        bitcount = 0
        byte = 0

        for bit in self.bit_buffer_output:
            byte = (byte << 1) | bit if bitcount % 8 else bit
            bitcount += 1

            if bitcount == 8:
                self.frame_buffer.append(byte)
                bitcount = 0
                byte = 0

    def cleanup_framebuffer(self):
        if len(self.frame_buffer) == 0:
            return
        
        # catch any syncwords that may appear due to errors of double sync words being sent
        if self.frame_buffer[0] == 0x7e: #and len(self.frame_buffer) > 0:
            self.frame_buffer.pop(0)
        if self.frame_buffer[-1] == 0x7e: #and len(self.frame_buffer) > 0:
            self.frame_buffer.pop()

    def reset_state(self):

        self.bit_buffer_input = []
        self.bit_buffer_output = []
        self.frame_buffer = []
        # self.active_frame = False
        self.ones = 0
    

