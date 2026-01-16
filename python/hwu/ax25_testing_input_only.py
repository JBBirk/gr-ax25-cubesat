#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import pmt
from gnuradio import gr
from .ax25_transceiver import Transceiver

class ax25_testing_input_only(gr.basic_block):
    """
    For testing purposes only, build frames but doesn't receive anything.
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
                retries=10):
        
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
        self.message_port_register_out(pmt.intern('Frame out'))

        self.transceiver.uplinker.start()
        self.transceiver.downlinker.start()
        self.transceiver.timers.start()
        self.transceiver.logger.debug("AX25 Testing Input Only block initialized")

    def handle_payload_in(self, msg_pmt):
        self.transceiver.logger.debug("Payload received")
        try:
            with self.transceiver.lock:
                self.transceiver.framequeue.append(
                    {"Dest":[self.transceiver.dest_addr,
                            self.transceiver.dest_ssid],
                            "Type":'I',
                            "Poll":False,
                            "Payload": bytes(pmt.u8vector_elements(pmt.cdr(msg_pmt))),
                            "Com":'COM'} #TODO: Looak at Payload handling, this might be a vector
                    )
        except ValueError as e: 
            self.transceiver.logger.debug(e)
        except Exception as e:
            self.transceiver.logger.debug(e)
