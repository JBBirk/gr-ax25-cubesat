#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
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


import bitstring as bs
import threading
import socket
import logging

from .ax25_framer import Framer
from .ax25_constants import PID
from .ax25_connectors import Uplinker, Downlinker



s_print_lock = threading.Lock()

def s_print(*a, **b):
    """Thread safe print function"""
    with s_print_lock:
        print(*a, **b)

""" Transceiver state machine class and methods """
class Transceiver:

    HOST = '127.0.0.1'
    PORT = 50056

    """ CONSTRUCTOR """
    """ Set AX.25 defined parameters """
    def __init__(self, src_addr='HWUGND',
                src_ssid=0b0001,
                dest_addr='HWUGND',
                dest_ssid=0b0010,
                full_duplex=False,
                rej='SREJ',
                modulo=8,
                information_field_length=2048, 
                receive_window_k=7, 
                ack_timer=3, 
                retries=10,
                gr_block=None):
        
        self.src_addr = src_addr
        self.src_ssid = src_ssid
        self.full_duplex = full_duplex
        self.rej = rej
        self.modulo = modulo
        self.information_field_length = information_field_length
        if receive_window_k <= self.modulo:
            self.receive_window_k = receive_window_k
        else:
            s_print("Window size k: %i bigger than avilable modulo %i. Reverting to default k=8" % (receive_window_k, self.modulo))
            self.receive_window_k = 7
        self.ack_timer = ack_timer
        self.retries = retries
        self.pid = bs.Bits(hex=PID)
        # self.tcp_isServer = tcp_isServer

        """ Setup internal links to other classes"""
        self.framer = Framer(self)
        self.uplinker = Uplinker(self, self.framer)
        self.downlinker = Downlinker(self, self.framer)
        self.gr_block = gr_block

        """ Setup helpers"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.framequeue = []
        self.frame_input_queue = []
        frame_output_queue = []
        self.lock = threading.Lock()
        self.frame_backlog = [0 for num in range(self.receive_window_k)]
        self.ns_before_seqbreak = 0
    

        """ Set internal variables """
        self.state = 'DISC'
        self.rej_active = 0
        self.send_state = 0
        self.receive_state = 0
        self.ack_state = 0

        """ Declare remote transceiver address and ssid for connecting procedures"""
        self.dest_addr = dest_addr
        self.dest_ssid = dest_ssid
        """ Set remote receivers busy state to False"""
        self.remote_busy = False

        """ Setup logger """

        self.logger = logging.getLogger(f"{__name__}.{self.src_addr}")
        # self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.hasHandlers():
            self.fh = logging.FileHandler(f'ax25_{self.src_addr}.log', mode='w')
            self.fh.setLevel(logging.DEBUG)
            self.logger.addHandler(self.fh)

        """ Setup debugging/testing feature to drop frames""" #TODO: Remove at some point/rework!
        # self.debugging_drop_frame = [3,4,7]

    def get_state(self):
        return self.state
    
    def get_state_variables(self):
        return [self.send_state, self.receive_state, self.ack_state]
    
    def set_state(self, state):
        self.state = state

    def reset_variables(self):
        self.send_state = 0
        self.receive_state = 0
        self.ack_state = 0

    def set_remote_busy(self, state:bool):
        self.remote_busy = state

