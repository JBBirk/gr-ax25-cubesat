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

import pmt
from gnuradio import gr
from .ax25_transceiver import Transceiver

class ax25_procedures(gr.basic_block):
    """
    Block implementing the AX.25 TNC behaviour
    """
    def __init__(self, src_addr='GNDGND',
                src_ssid=0b0001,
                dest_addr='SATSAT',
                dest_ssid=0b0001,
                full_duplex=False,
                rej='SREJ',
                modulo=8,
                information_field_length=2048, 
                receive_window_k=7, 
                ack_timer=3, 
                retries=10, 
                #pid=bs.Bits(hex='0xF0'), 
                tcp_isServer=False):
        

        gr.basic_block.__init__(self,
            name="AX25_main_procedures_block",
            in_sig=None,
            out_sig=None)
        
        self.transceiver = Transceiver(src_addr, 
                                       src_ssid,
                                       dest_addr,
                                       dest_ssid, 
                                       full_duplex, 
                                       rej, 
                                       modulo, 
                                       information_field_length, 
                                       receive_window_k,
                                       ack_timer,
                                       retries,
                                       gr_block=self)
        
    
        self.message_port_register_in(pmt.intern('Payload in'))
        self.set_msg_handler(pmt.intern('Payload in'), self.handle_payload_in)
        self.message_port_register_in(pmt.intern('Frame in'))
        self.set_msg_handler(pmt.intern('Frame in'), self.handle_frame_in)
        self.message_port_register_out(pmt.intern('Frame out'))
        self.message_port_register_out(pmt.intern('Payload out'))

        self.transceiver.uplinker.start()
        self.transceiver.downlinker.start()
        self.transceiver.timers.start()


    def handle_payload_in(self, msg_pmt):
        try:
            with self.transceiver.lock:
                self.transceiver.framequeue.append(
                    {"Dest":[self.transceiver.dest_addr,
                            self.transceiver.dest_ssid],
                            "Type":'I',
                            "Poll":False,
                            "Payload": bytes(pmt.u8vector_elements(pmt.cdr(msg_pmt))),
                            "Com":'COM'}
                    )
        except ValueError as e: 
            self.transceiver.logger.debug(e)
        except Exception as e:
            self.transceiver.logger.debug(e)

    def handle_frame_in(self, msg_pmt):
        try:
            with self.transceiver.lock:
                self.transceiver.frame_input_queue.append(msg_pmt)
        except ValueError as e: 
            self.transceiver.logger.debug(e)
        except Exception as e:
            self.transceiver.logger.debug(e)
