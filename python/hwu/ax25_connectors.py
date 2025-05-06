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
        except:
            self.transceiver.logger.debug("Something went wrong")


    def _run(self) -> None:

        # frames_sent = 0
        while not self._kill.isSet():
        # with self.transceiver.lock:
            self.transceiver.lock.acquire()
            if self.transceiver.framequeue:
                request = self.transceiver.framequeue[0]
                # print("received payload: ", request)
                # okay_to_send = 
                
                # Check whether receive window would be exceeded 
                if request["Type"] == 'I' and self.transceiver.send_state == (self.transceiver.ack_state + self.transceiver.receive_window_k)%self.transceiver.modulo: #TODO Check if this interferes with recovery by blocking frames fomr sending
                    self.transceiver.logger.debug(f"Remote receive window full, waiting for clear. Acked: {self.transceiver.ack_state}, Sent: {self.transceiver.send_state}. Framequeue at {len(self.transceiver.framequeue)}")
                    # print("Receive window overflow")
                    self.transceiver.lock.release()
                    time.sleep(0.05)
                    continue
                else:
                    self.transceiver.framequeue.pop(0)
                    self.transceiver.lock.release()
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
                        self.transceiver.logger.debug("Framing falied!")
                        continue
                    self.send(raw_frame)
                    # with self.transceiver.lock:
                    # self.transceiver.framequeue.pop(0)
                    # time.sleep(0.5) #TODO: At some point remove these sleeps!
                        
            else:
                self.transceiver.lock.release()
                # time.sleep(0.5)            
                pass    


    def send(self, frame:bs.BitArray):

        byte_vector = [byte for byte in frame.tobytes()] #this does add 0 bits to the end as padding, should be removed later in flowgraph
        try:  
            self.transceiver.gr_block.message_port_pub(pmt.intern('Frame out'), pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(byte_vector), byte_vector)))
        except Exception as e:
            print(e)




""" Class to split up- and downlink and put them in separate threads"""
class Downlinker:

    def __init__(self, transceiver, framer) -> None:
        self._thread = threading.Thread(target=self._run, name="Downlinker Thread", daemon=True)
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
        except:
            self.transceiver.logger.debug("Something went wrong")
        
        

    def _run(self) -> None:
        # frames_received = 0
        while not self._kill.isSet(): #Replace buffer value late with real max value
            with self.transceiver.lock:
                if not self.transceiver.frame_input_queue:
                    time.sleep(0.01)
                    continue
                try:
                    raw_frame = bs.BitArray(bytes(pmt.u8vector_elements(pmt.cdr(self.transceiver.frame_input_queue.pop(0)))))
                except Exception as e:
                    self.transceiver.logger.warning(f"The following exception occured while receiving frame: {e}")
            # while raw_frame[-2:] != '0b10': #removing padding from frame. Not needed since introduction of frame extractor
            #     raw_frame = raw_frame[:-1]

            # frames_received += 1
            # time.sleep(0.1)
            # if frames_received in self.transceiver.debugging_drop_frame:      #Old test to see, what happens when a frame is dropped
            #     continue

            try:
                data = self.framer.deframe(raw_frame)
                self.transceiver.logger.debug(f"Raw Frame received: {raw_frame.hex}, Decoded Frame: {data}")
            except TypeError:
                self.transceiver.logger.debug("Something went wrong while deframing!")
                continue
            
            # self.transceiver.logger.debug(f"Data Frame received: {data}")
            if data['Type'] == 'ERROR':
                # print("Error Received")
                self.transceiver.logger.warning("=========== Internal Error occured, see last log entry ===========")
                self.transceiver.logger.warning("")
                # time.sleep(0.5)
                continue

            if data['Type'] == 'RECOVERY':
                self.__RECOVERY_handler(data)
                continue

            if data['Type'] == 'I':
                self.__I_frame_handler(data)
                continue

            if data['Type'] == 'REJ':
                self.__REJ_frame_handler(data)
                continue

            if data['Type'] == 'SREJ':
                self.__SREJ_frame_handler(data)
                continue

            if data['Type'] == 'RR':
                self.__RR_frame_handler(data)
                continue

            if data['Type'] == 'RNR':
                self.__RNR_frame_handler(data)
                continue

            self.transceiver.logger.warning("Should never get here!")
            raise RuntimeError

    def __I_frame_handler(self, data):

        #Insert actual handling of data here, when implemented differently
        # self.transceiver.logger.debug(data["Pid-Data"][8:].tobytes())# .decode())
        byte_vec = [byte for byte in data["Pid-Data"][8:].tobytes()]

        # self.transceiver.logger.debug("Answering to message")
        try:
            self.transceiver.logger.debug(f"Successfully received Data: {byte_vec}")
            self.transceiver.gr_block.message_port_pub(pmt.intern("Payload out"), pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(byte_vec), byte_vec)))
        except Exception as e:
            print(e)
        # s_print(data["Pid-Data"][8:].tobytes().decode())

        with self.transceiver.lock:
            self.transceiver.receive_state = (self.transceiver.receive_state + 1)%self.transceiver.modulo
            self.transceiver.ack_state = data["Nr"] # N(r)
            if self.transceiver.rej_active and data["Ns"] == self.transceiver.ns_before_seqbreak-1 and self.transceiver.rej == "REJ":
                self.transceiver.rej_active = 0
                self.transceiver.logger.debug("REJ Recovery finished, all missing frames received")
            if not self.transceiver.framequeue or self.transceiver.send_state == (self.transceiver.ack_state + self.transceiver.receive_window_k)%self.transceiver.modulo:
                self.transceiver.framequeue.insert(0,{"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RNR' if self.transceiver.state == 'BUSY' else 'RR', "Poll":False, "Payload": None, "Com": 'COM'})
    
    def __RECOVERY_handler(self, data):
        self.transceiver.logger.debug(f"Sequence Error occured, now in {self.transceiver.rej} recovery!") if not self.transceiver.rej_active else self.transceiver.logger.debug(f"Still in {self.transceiver.rej} recovery!")
        if self.transceiver.rej_active == 1 and data["Poll"] == True: #Anser to Poll while already in reject mode (is counter for SREJ)
            self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RR', "Poll":True, "Payload": None, "Com": 'COM'})
            return None
        
        with self.transceiver.lock:
            if self.transceiver.rej == "REJ":
                if self.transceiver.rej_active != 1:
                # if self.transceiver.rej_active != 1: # Don't resend REJ frame if already happend, or it will mess up the procedure
                    self.transceiver.ns_before_seqbreak = data["Ns"]
                    self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'REJ', "Poll":data["Poll"], "Payload": None, "Com":'COM'})
                    self.transceiver.rej_active = 1

                return None
        
            elif self.transceiver.rej == "SREJ":
                return
        
        # Should never get here
        self.transceiver.logger.warning("Error in the recovery setup, neither REJ nor SREJ properly setup! Reverting to REJ as default!")
        self.transceiver.rej = "REJ"
        return None
    
    def __REJ_frame_handler(self, data):
        iters = 0
        with self.transceiver.lock:
            self.transceiver.set_remote_busy(False)
            if data["Com"] == 'COM' and data["Poll"] == True:
                self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RR', "Poll":True, "Payload": None, "Com": 'RES'}) #TODO: double check if this is really and RES frame. Not in doc but should be form my understanding

            sendstate_at_rej = self.transceiver.get_state_variables()[0]
            self.transceiver.send_state = data["Nr"]
            self.transceiver.logger.debug(f"Offset, transceiver at: {sendstate_at_rej}, remote expected: {data['Nr']}")
            
            while (data["Nr"] + iters)%self.transceiver.modulo != sendstate_at_rej:
                self.transceiver.framequeue.insert(iters, self.transceiver.frame_backlog[(data["Nr"]+iters)%self.transceiver.modulo])
                self.transceiver.logger.debug(f"Added frame from backlog pos {(data['Nr']+iters)%self.transceiver.modulo} to framequeue at pos {iters}")
                iters += 1
            # for iters in range(sendstate_at_rej-data["Nr"]): #TODO this fails when crossing over state from 7 to 0
            #     self.transceiver.framequeue.insert(iters, self.transceiver.frame_backlog[data["Nr"]+iters])
            #     self.transceiver.logger.debug(f"Added frame from backlog pos {data['Nr']+iters} to framequeue at pos {iters}")

        return None
    
    def __SREJ_frame_handler(self, data):


        return None
    
    def __RR_frame_handler(self, data):
        if data["Nr"] != self.transceiver.ack_state: # Address this, as first frame has nr of 0 and will not change ack state
            self.transceiver.ack_state = data["Nr"]  # -> Should be fixed, V(a) is now equal to remotes V(r) and thus received N(r) 
        if data["Poll"] == False:                    # -> First frame overall can't ack anything, so this is correct!
            return
        self.transceiver.set_remote_busy = False

    
    def __RNR_frame_handler(self, data):
        
        if data[1] == False:
            return
        self.transceiver.set_remote_busy = True
        
