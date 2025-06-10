#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
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
from gnuradio import gr

class nrzi_decode_packed(gr.sync_block):
    """
    NRZI decoding  following HDLC standard (transition on 0) for packed bytes
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name="nrzi_decode_packed",
            in_sig=[np.uint8],
            out_sig=[np.uint8])
        
    def assemble_byte(self, input:list) -> list:
        bitcount = 0
        byte = 0
        assembled = []

        for bit in input:
            byte = (byte << 1) | bit #if bitcount % 8 else bit #Remnants from earlier implementation
            bitcount += 1

            if 8 == bitcount:
                assembled.append(byte)
                bitcount = 0
                byte = 0
        
        return assembled


    def work(self, input_items, output_items):
        in0 = input_items[0]

        bit = 0
        prev_bit = 0
        currentstate = 0
        decodedlist = []

        for byte in in0:
            for i in range(8):
                bit = (byte >> (7-i)) & 0x1
                currentstate = 1 if bit == prev_bit else 0
                decodedlist.append(currentstate)
                prev_bit = bit

        decodedlist = self.assemble_byte(decodedlist)

        output_items[0][:] = decodedlist[:]

        return len(output_items[0])

