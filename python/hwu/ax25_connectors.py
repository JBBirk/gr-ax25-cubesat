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

import time
import threading
import bitstring as bs
import pmt

""" Class to split up- and downlink and put them in separate threads"""
class Uplinker:


    def __init__(self, transceiver, framer) -> None:
        self._thread = threading.Thread(target=self._run, name="Uplinker Thread", daemon=True)
        self._running = threading.Event()
        self._kill = threading.Event()
        self._lock = threading.Lock()
        self.transceiver = transceiver
        self.framer = framer


    def start(self) -> None:
        
        try:
            with self._lock:
                if not self._thread.is_alive():
                    self._thread.start()
                if not self._running.is_set():
                    self._running.set()
        except Exception as e:
            self.transceiver.logger.warning(f"Could not start uplinker thread due to {e}")

    """ Uplinker Main Run Loop """
    def _run(self) -> None:
        
        while not self._kill.isSet():

            self.transceiver.lock.acquire()
            if self.transceiver.framequeue:
                start_time = time.time()
                request = self.transceiver.framequeue.pop(0)
                self.transceiver.lock.release()

                # Check whether receive window would be exceeded 
                if request["Type"] == 'I' and self.transceiver.get_state_variable('vs') == (self.transceiver.get_state_variable('va') + self.transceiver.receive_window_k)%self.transceiver.modulo: #TODO Check if this interferes with recovery by blocking frames fomr sending
                    with self.transceiver.lock:
                        self.transceiver.framequeue.insert(0, request)
                    self.transceiver.logger.debug(f"Remote receive window full, waiting for clear. Acked: {self.transceiver.get_state_variable('va')}, Sent: {self.transceiver.get_state_variable('vs')}") # Framequeue at {len(self.transceiver.framequeue)}")
                    time.sleep(0.1) #TODO rework waiting procedure
                    continue

                else:
                    raw_frame = self.framer.frame(
                                            request["Type"], #Frametype
                                            self.transceiver.src_addr,
                                            self.transceiver.src_ssid,
                                            request["Dest"][0], #destination address
                                            request["Dest"][1], #destination ssid
                                            self.transceiver.pid,
                                            request["Payload"], #Payload data
                                            request["Com"],
                                            self.transceiver.modulo,
                                            request["Poll"] #Poll/Final
                                            )
                    
                    if raw_frame is None:
                        self.transceiver.logger.debug("Framing failed!")
                        continue

                    self.send(raw_frame)
                    send_time = time.time() - start_time 
                    self.transceiver.timing_logger.debug("Sending " + request["Type"] + f" frame took {send_time*1000:.2f}ms")
                    time.sleep(0.01)
                    if request["Type"] == 'I':
                        self.transceiver.timer_reset_t1.set()
                        
            else: #framequeue empty
                self.transceiver.lock.release()
                time.sleep(0.01)            
                continue    


    def send(self, frame:bs.BitArray):

        byte_vector = [byte for byte in frame.tobytes()] #this does add 0 bits to the end as padding, should be removed later in flowgraph. Although not strictly necessary
        try:  
            self.transceiver.gr_block.message_port_pub(pmt.intern('Frame out'), pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(byte_vector), byte_vector)))
        except Exception as e:
            self.transceiver.logger.warning(f"exception occured when trying to send frame: {e}")




""" Class to split up- and downlink and put them in separate threads"""
class Downlinker:

    def __init__(self, transceiver, framer) -> None:
        self._thread = threading.Thread(target=self._run, name="Downlinker Thread", daemon=True)
        self._running = threading.Event()
        self._kill = threading.Event()
        self._lock = threading.Lock()
        self.transceiver = transceiver
        self.framer = framer
        
        self.setup_handlers()

    """ Setup dict of handler functions to call depending on frame type """
    def setup_handlers(self):
        self.handler_functions = {}
        for attr in dir(self):
            if attr.endswith("handler"):
                self.handler_functions.setdefault(attr[13:-14], getattr(self, attr))
        
    
    """ Start Downlinker Thread"""
    def start(self) -> None:
         
        try:
            with self._lock:
                if not self._thread.is_alive():
                    self._thread.start()
                if not self._running.is_set():
                    self._running.set()
        except Exception as e:
            self.transceiver.logger.warning(f"Could not start downlinker thread, due to {e}")
        
        
    """ Downlinker Main Run loop"""
    def _run(self) -> None:



        while not self._kill.isSet():
            self.transceiver.lock.acquire()
            if not self.transceiver.frame_input_queue:
                self.transceiver.lock.release()
                time.sleep(0.01) # TODO: Rework waiting for frame procedure
                continue
            try:
                start_time = time.time()
                raw_frame = bs.BitArray(bytes(pmt.u8vector_elements(pmt.cdr(self.transceiver.frame_input_queue.pop(0)))))
                self.transceiver.lock.release()
            except Exception as e:
                self.transceiver.lock.release()
                self.transceiver.logger.warning(f"The following exception occured while receiving frame: {e}")

                continue
            
            try:
                data = self.framer.deframe(raw_frame)
                self.transceiver.logger.debug(f"Raw Frame received: {raw_frame.hex}, Decoded Frame: {data}")
            except Exception as e:
                self.transceiver.logger.warning(f"The following error occured while deframing: {e}")
                continue

            try:
                self.handler_functions[data['Type']](data)
                self.transceiver.timing_logger.debug(f"Answering to {data['Type']} frame took {(time.time() - start_time)*1000:.2f}ms")
            except:
                self.transceiver.logger.warning(f"No correspondig handler for frame type {data['Type']}")
    

    def __ERROR_frame_handler(self, data):
                self.transceiver.logger.warning("=========== Internal Error occured, see last log entry ===========")
                self.transceiver.logger.warning("")

    def __I_frame_handler(self, data):
        if data["Poll"]: #Respond correctly to Poll typ
            poll_state = True
        else:
            poll_state = False

            self.__acknowledgement_handler(data)

        byte_vec = [byte for byte in data["Pid-Data"][8:].tobytes()]

        try:
            self.transceiver.logger.debug(f"Successfully received Data: {byte_vec}")
            self.transceiver.gr_block.message_port_pub(pmt.intern("Payload out"), pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(byte_vec), byte_vec)))
        except Exception as e:
            self.logger.warning(f"Exception occured during payload out: {e}")

        if self.transceiver.get_remote_busy():
            self.transceiver.timer_reset_t3.set()

        # Update internal state variables
        self.transceiver.set_state_variable("vr", (self.transceiver.get_state_variable("vr") + 1)%self.transceiver.modulo)

        # Check if all lost frames have been recovered
        if self.transceiver.get_rej_active() and data["Ns"] == self.transceiver.get_ns_before_seqbreak()-1 and self.transceiver.rej == "REJ":
            self.transceiver.set_rej_active(0)
            self.transceiver.logger.debug("REJ Recovery finished, all missing frames received")

        # Add supervisory frame response if needed (No I-frames in frame queue, remote receive window full)
        if not self.transceiver.framequeue or self.transceiver.get_state_variable('vs') == (self.transceiver.get_state_variable('va') + self.transceiver.receive_window_k)%self.transceiver.modulo:
            busy_state = self.transceiver.get_state() == 'BUSY'
            with self.transceiver.lock:
                self.transceiver.framequeue.insert(0,
                                                    {"Dest":[self.transceiver.dest_addr,
                                                            self.transceiver.dest_ssid],
                                                            "Type":'RNR' if busy_state else 'RR',
                                                            "Poll":poll_state,
                                                            "Payload": None,
                                                            "Com": 'COM'})
    
    def __RECOVERY_frame_handler(self, data):
 
        if not self.transceiver.get_rej_active():
            self.transceiver.logger.debug(f"Sequence Error occured, now in {self.transceiver.rej} recovery!")
        else:
            self.transceiver.logger.debug(f"Still in {self.transceiver.rej} recovery!")

        if self.transceiver.get_rej_active() and data["Poll"]: #Anser to Poll while already in reject mode. Needed for recovery of a lost REJ frame, expected when Timer T1 runs out
            with self.transceiver.lock:
                self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'REJ', "Poll":True, "Payload": None, "Com": 'COM'})

        if self.transceiver.rej == "REJ":
            if not self.transceiver.get_rej_active(): # Don't resend REJ frame if already happend, or it will mess up the procedure
                self.transceiver.set_ns_before_seqbreak(data["Ns"])
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'REJ', "Poll":data["Poll"], "Payload": None, "Com":'COM'})
                self.transceiver.set_rej_active(1)

            return None
    
        elif self.transceiver.rej == "SREJ":
            self.transceiver.logger.warning("SREJ type error handling not implemented yet!")
            return
        
        # Should never get here
        self.transceiver.logger.warning("Error in the recovery setup, neither REJ nor SREJ properly setup! Reverting to REJ as default!")
        self.transceiver.rej = "REJ"
        return None
    
    def __REJ_frame_handler(self, data):

        self.__acknowledgement_handler(data)

        self.transceiver.set_remote_busy(False)

        sendstate_at_rej = self.transceiver.get_state_variable('vs')
        self.transceiver.set_state_variable('vs', data["Nr"])
        self.transceiver.logger.debug(f"Offset, transceiver at: {sendstate_at_rej}, remote expected: {data['Nr']}")

        for iters in range((sendstate_at_rej - data["Nr"])%self.transceiver.modulo):
            with self.transceiver.lock:
                self.transceiver.framequeue.insert(iters, self.transceiver.frame_backlog[(data["Nr"]+iters)%self.transceiver.modulo])
            self.transceiver.logger.debug(f"Added frame from backlog pos {(data['Nr']+iters)%self.transceiver.modulo} to framequeue at pos {iters}")

        return None
    
    def __SREJ_frame_handler(self, data):


        return None
    
    def __RR_frame_handler(self, data):
        
        self.transceiver.set_remote_busy(False)

        self.__acknowledgement_handler(data)
                                                
        if data["Poll"] == True and self.transceiver.get_t1_try_count() == 0: #Answer to Poll coming from remote
            self.transceiver.logger.debug("Poll frame received, answering")

            self.transceiver.set_ns_before_seqbreak(self.transceiver.get_state_variable("vr")) #Assume sequence break. Needed for REJ handling
            self.transceiver.set_rej_active(1)

            if self.transceiver.get_state() == 'BUSY':
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RNR', "Poll":True, "Payload": None, "Com": 'RES'})
                return
            else:
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RR', "Poll":True, "Payload": None, "Com": 'RES'})
                return
            
        
        elif data["Poll"] == True and self.transceiver.get_t1_try_count() != 0: # final response to poll, act accrordingly

            self.transceiver.logger.debug("Final frame received, answering")
            self.transceiver.set_t1_try_count(0)
            if self.transceiver.get_state_variable("va") == self.transceiver.get_state_variable("vs"): # No lost frames
                return
            
            #Actual missing frames, retransmit. Same procedure as in __REJ_frame_handler
            sendstate_at_rej = self.transceiver.get_state_variable('vs')
            self.transceiver.set_state_variable('vs', data["Nr"])
            self.transceiver.logger.debug(f"Offset, transceiver at: {sendstate_at_rej}, remote expected: {data['Nr']}")
                
            for iters in range((sendstate_at_rej - data["Nr"])%self.transceiver.modulo):
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(iters, self.transceiver.frame_backlog[(data["Nr"]+iters)%self.transceiver.modulo])
                self.transceiver.logger.debug(f"Added frame from backlog pos {(data['Nr']+iters)%self.transceiver.modulo} to framequeue at pos {iters}")
                    

        return
        

    
    def __RNR_frame_handler(self, data): #TODO T3 start/stop

        self.transceiver.set_remote_busy(True)

        self.__acknowledgement_handler(data)                           

        if data["Poll"] == True and self.transceiver.get_t1_try_count() == 0: #Answer to Poll coming from remote
            if self.transceiver.get_state() == 'BUSY':
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RNR', "Poll":True, "Payload": None, "Com": 'RES'})
                return
            else:
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RR', "Poll":True, "Payload": None, "Com": 'RES'})
                return
            
        
        elif data["Poll"] == True and self.transceiver.get_t1_try_count() != 0: # final response to poll, act accrordingly
            
            self.transceiver.set_t1_try_count(0)
            if self.transceiver.get_state_variable("va") == self.transceiver.get_state_variable("vs"): # No lost frames
                return
            
            #Actual missing frames, retransmit. Same procedure as in __REJ_frame_handler
            sendstate_at_rej = self.transceiver.get_state_variable('vs')
            self.transceiver.set_state_variable('vs', data["Nr"])
            self.transceiver.logger.debug(f"Offset, transceiver at: {sendstate_at_rej}, remote expected: {data['Nr']}")

            for iters in range((sendstate_at_rej - data["Nr"])%self.transceiver.modulo):
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(iters, self.transceiver.frame_backlog[(data["Nr"]+iters)%self.transceiver.modulo])
                self.transceiver.logger.debug(f"Added frame from backlog pos {(data['Nr']+iters)%self.transceiver.modulo} to framequeue at pos {iters}")
                
            return
        return


    def __acknowledgement_handler(self, data):

        if data["Nr"] == self.transceiver.get_state_variable("va"): return # No new frames have been acknolwedged, nothin to do
                
        if data["Nr"] == self.transceiver.get_state_variable("vs"): #All sent frames are acknowledged, stop timer t1
            self.transceiver.timer_cancel_t1.set()
        else: #Some new frames have been acknowledged, but not all, reset timer t1
            self.transceiver.timer_reset_t1.set()

        self.transceiver.set_state_variable("va", data["Nr"]) # = data["Nr"] # Update acknowledgement state variable

        return


            
                

        
