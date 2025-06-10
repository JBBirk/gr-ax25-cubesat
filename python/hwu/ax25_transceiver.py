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
import time

from .ax25_framer import Framer
from .ax25_constants import PID
from .ax25_connectors import Uplinker, Downlinker
from .ax25_timers import Timers



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
                timer_t1_seconds=3,
                timer_t3_seconds=10,
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
        self.timer_reset_t1 = threading.Event()
        self.timer_cancel_t1 = threading.Event()
        self.timer_reset_t3 = threading.Event()
        self.timer_cancel_t3 = threading.Event()
        self.t1_try_count = 0
        self.t3_try_count = 0
        # self.tcp_isServer = tcp_isServer

        """ Setup internal links to other classes"""
        self.framer = Framer(self)
        self.uplinker = Uplinker(self, self.framer)
        self.downlinker = Downlinker(self, self.framer)
        self.gr_block = gr_block

        self.timers = Timers(self, self.timer_reset_t1, self.timer_cancel_t1, self.timer_reset_t3, self.timer_cancel_t3, timer_t1_seconds, timer_t3_seconds)

        """ Setup helpers"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.framequeue = []
        self.frame_input_queue = []
        # frame_output_queue = []  Not actually used
        self.lock = threading.Lock()
        self.framequeue_not_empty = threading.Condition(self.lock)
        self.frame_input_queue_not_empty = threading.Condition(self.lock)
        # self.lock = TrackingLock("Transceiver_Lock")
        self.frame_backlog = [0 for num in range(self.receive_window_k)]
        self.ns_before_seqbreak = 0
        self.awaiting_final = False # Response to a Poll bit
    

        """ Set internal variables """
        self.state = 'DISC'
        self.rej_active = 0
        # self.send_state = 0
        # self.receive_state = 0
        # self.ack_state = 0
        self.state_variables = {'vs': 0, 'vr': 0, 'va': 0}

        """ Declare remote transceiver address and ssid for connecting procedures"""
        self.dest_addr = dest_addr
        self.dest_ssid = dest_ssid
        """ Set remote receivers busy state to False"""
        self.remote_busy = False

        """ Setup logger """

        self.logger = logging.getLogger(f"{__name__}.{self.src_addr}")
        # self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # if not self.logger.hasHandlers():
        self.fh = logging.FileHandler(f'ax25_{self.src_addr}.log', mode='w')
        self.fh.setLevel(logging.DEBUG)
        self.logger.addHandler(self.fh)

        self.timing_logger = logging.getLogger(f"{__name__}.{self.src_addr}.timing")
        self.timing_logger.setLevel(logging.DEBUG)
        timing_file = logging.FileHandler(f'ax25_{self.src_addr}_timing.log', mode='w')
        timing_file.setLevel(logging.DEBUG)
        self.timing_logger.addHandler(timing_file)


    """ Thread safe getters and setters for different transceiver variables """
    def get_state(self):
        with self.lock:
            return self.state
    
    def get_state_variable(self, key):
        with self.lock:
            return self.state_variables.get(key)
    
    def set_state(self, state):
        with self.lock:
            self.state = state

    def set_state_variable(self, key, value):
        with self.lock:
            self.state_variables[key] = value
            return

    def reset_variables(self):
        with self.lock:
            self.send_state = 0
            self.receive_state = 0
            self.ack_state = 0
            self.state_variables = {'vs': 0, 'vr': 0, 'va': 0}
            return

    def set_remote_busy(self, state:bool):
        with self.lock:
            self.remote_busy = state
    
    def get_remote_busy(self):
        with self.lock:
            return self.remote_busy
        
    def set_rej_active(self, state:bool):
        with self.lock:
            self.rej_active = state

    def get_rej_active(self):
        with self.lock:
            return self.rej_active
        
    def set_ns_before_seqbreak(self, ns:int):
        with self.lock:
            self.ns_before_seqbreak = ns

    def get_ns_before_seqbreak(self):
        with self.lock:
            return self.ns_before_seqbreak
        
    def get_t1_try_count(self):
        with self.lock:
            return self.t1_try_count
        
    def set_t1_try_count(self, count:int):
        with self.lock:
            self.t1_try_count = count

    def get_t3_try_count(self):
        with self.lock:
            return self.t3_try_count
        
    def set_t3_try_count(self, count:int):
        with self.lock:
            self.t3_try_count = count

    # def get_timer_states(self):
    #     pass


# class TrackingLock:
#     def __init__(self, name):
#         self.name = name
#         self.lock = threading.Lock()
#         self.locals = threading.local()
#         self.locals.holder  = None
#         self.locals.acquire_time = None
#         self.lock_logger = logging.getLogger("LOCKS")
#         self.lock_logger.setLevel(logging.DEBUG)
#         # if not self.logger.hasHandlers():
#         self.fh = logging.FileHandler('ax25_locks.log', mode='w')
#         self.fh.setLevel(logging.DEBUG)
#         self.lock_logger.addHandler(self.fh)

#     def acquire(self, blocking=True):
#         if self.lock.acquire(blocking):
#             # self.lock.acquire(blocking)
#             self.locals.holder = threading.current_thread().name
#             self.locals.acquire_time = time.time()
#             self.lock_logger.info(30*"=")
#             self.lock_logger.info(f"Lock '{self.name}' acquired by thread '{self.locals.holder}'")
#             return True
#         return False

#     def release(self):
#         if self.locals.holder == threading.current_thread().name:
#             hold_time = time.time() - self.locals.acquire_time
#             self.lock.release()
#             self.lock_logger.info(f"Lock '{self.name}' released by thread '{self.locals.holder}' after {round(hold_time*1000)} ms")
#             self.lock_logger.info(30*"=")
#             self.locals.holder = None
#             self.locals.acquire_time = None
#         else:
#             pass
#             self.lock_logger.error(f"Thread '{threading.current_thread().name}' tried to release lock '{self.name}' held by thread '{self.locals.holder}'")
#             self.lock_logger.info(30*"=")

#     def __enter__(self):
#         self.acquire()
#         return self

#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.release()


