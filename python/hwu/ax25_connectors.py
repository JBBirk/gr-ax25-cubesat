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
        # with self.transceiver.lock:
            self.transceiver.lock.acquire()
            if self.transceiver.framequeue:
                start_time = time.time()
                # request = self.transceiver.framequeue[0]
                request = self.transceiver.framequeue.pop(0)
                self.transceiver.lock.release()
                # Check whether receive window would be exceeded 
                # if request["Type"] == 'I' and self.transceiver.send_state == (self.transceiver.ack_state + self.transceiver.receive_window_k)%self.transceiver.modulo: #TODO Check if this interferes with recovery by blocking frames fomr sending
                if request["Type"] == 'I' and self.transceiver.get_state_variable('vs')== (self.transceiver.get_state_variable('va') + self.transceiver.receive_window_k)%self.transceiver.modulo: #TODO Check if this interferes with recovery by blocking frames fomr sending
                    with self.transceiver.lock:
                        self.transceiver.framequeue.insert(0, request)
                    self.transceiver.logger.debug(f"Remote receive window full, waiting for clear. Acked: {self.transceiver.get_state_variable('va')}, Sent: {self.transceiver.get_state_variable('vs')}") # Framequeue at {len(self.transceiver.framequeue)}")
                    # print("Receive window overflow")
                    # self.transceiver.lock.release()
                    time.sleep(0.1) #TODO rework waiting procedure
                    continue
                else:
                    # self.transceiver.framequeue.pop(0)
                    # self.transceiver.lock.release()
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
                    # framing_time = time.time() - start_time
                    if raw_frame is None:
                        self.transceiver.logger.debug("Framing failed!")
                        continue
                    self.send(raw_frame)
                    send_time = time.time() - start_time 
                    self.transceiver.timing_logger.debug("Sending " + request["Type"] + f" frame took {send_time*1000:.2f}ms")
                    if request["Type"] == 'I':
                        # self.transceiver.logger.debug("Pre T1 reset")
                        self.transceiver.timer_reset_t1.set()
                        # self.transceiver.logger.debug("Post T1 reset")
                        
            else: #framequeue empty
                self.transceiver.lock.release()
                time.sleep(0.01)            
                continue    


    def send(self, frame:bs.BitArray):

        byte_vector = [byte for byte in frame.tobytes()] #this does add 0 bits to the end as padding, should be removed later in flowgraph. ALthough not strictly necessary
        try:  
            self.transceiver.gr_block.message_port_pub(pmt.intern('Frame out'), pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(byte_vector), byte_vector)))
            # self.transceiver.logger.debug(f"Successfully pushed frame: {pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(byte_vector), byte_vector))}")
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

        testing_num_frames = 0

        while not self._kill.isSet():
            self.transceiver.lock.acquire()
            if not self.transceiver.frame_input_queue:
                self.transceiver.lock.release()
                time.sleep(0.01) # TODO: Rework waiting for frame procedure
                # self.transceiver.lock.release()
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
                testing_num_frames += 1
            except Exception as e:
                self.transceiver.logger.warning(f"The following error occured while deframing: {e}")
                continue

            # TODO: Rework to use dict insted of if chain
            # self.transceiver.logger.debug(f"Data Frame received: {data}")
            # if data['Type'] == 'ERROR':
            #     # print("Error Received")
            #     self.transceiver.logger.warning("=========== Internal Error occured, see last log entry ===========")
            #     self.transceiver.logger.warning("")
            #     # time.sleep(0.5)
            #     continue
            if testing_num_frames == 2: #For testing only, drop first received frame
                self.transceiver.logger.debug(f"Second frame dropped")
                continue

            try:
                self.handler_functions[data['Type']](data)
                self.transceiver.timing_logger.debug(f"Answering to {data['Type']} frame took {(time.time() - start_time)*1000:.2f}ms")
            except:
                self.transceiver.logger.warning(f"No correspondig handler for frame type {data['Type']}")

            # Old implemetation, just kept as backup (I know it's a mess)

            # if data['Type'] == 'RECOVERY':
            #     self.__RECOVERY_frame_handler(data)
            #     continue

            # if data['Type'] == 'I':
            #     self.__I_frame_handler(data)
            #     continue

            # if data['Type'] == 'REJ':
            #     self.__REJ_frame_handler(data)
            #     continue

            # if data['Type'] == 'SREJ':
            #     self.__SREJ_frame_handler(data)
            #     continue

            # if data['Type'] == 'RR':
            #     self.__RR_frame_handler(data)
            #     continue

            # if data['Type'] == 'RNR':
            #     self.__RNR_frame_handler(data)
            #     continue

            # self.transceiver.logger.warning("Should never get here!")
            # raise RuntimeError
    

    def __ERROR_frame_handler(self, data):
                self.transceiver.logger.warning("=========== Internal Error occured, see last log entry ===========")
                self.transceiver.logger.warning("")

    def __I_frame_handler(self, data):
        if data["Poll"]: #Respond correctly to Poll typ
            poll_state = True
        else:
            poll_state = False

            self.__acknowledgement_handler(data)

        #Insert actual handling of data here, when implemented differently

        # self.transceiver.logger.debug(data["Pid-Data"][8:].tobytes())# .decode())
        byte_vec = [byte for byte in data["Pid-Data"][8:].tobytes()]

        # self.transceiver.logger.debug("Answering to message")
        try:
            self.transceiver.logger.debug(f"Successfully received Data: {byte_vec}")
            self.transceiver.gr_block.message_port_pub(pmt.intern("Payload out"), pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(byte_vec), byte_vec)))
        except Exception as e:
            self.logger.warning(f"Exception occured during payload out: {e}")

        # with self.transceiver.lock:

        if self.transceiver.get_remote_busy():
            self.transceiver.timer_reset_t3.set()
            # if self.transceiver.remote_busy:
            #     self.transceiver.timer_reset_t3.set()

        self.transceiver.set_state_variable("vr", (self.transceiver.get_state_variable("vr") + 1)%self.transceiver.modulo)
            # Update internal state variables
            # self.transceiver.receive_state = (self.transceiver.receive_state + 1)%self.transceiver.modulo
            # self.transceiver.ack_state = data["Nr"] # N(r)



            # Check if all lost frames have been recovered
        # if self.transceiver.rej_active and data["Ns"] == self.transceiver.ns_before_seqbreak-1 and self.transceiver.rej == "REJ": 
        if self.transceiver.get_rej_active() and data["Ns"] == self.transceiver.get_ns_before_seqbreak()-1 and self.transceiver.rej == "REJ":
            # self.transceiver.rej_active = 0
            self.transceiver.set_rej_active(0)
            self.transceiver.logger.debug("REJ Recovery finished, all missing frames received")

            # Add supervisory frame response if needed (No I-frames in frame queue, remote receive window full)
        # if not self.transceiver.framequeue or self.transceiver.send_state == (self.transceiver.ack_state + self.transceiver.receive_window_k)%self.transceiver.modulo: #or self.transceiver.t1_try_count > 0:
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
        # with self.transceiver.lock:
            # if self.transceiver.rej_active == 1 and data["Poll"] == True: #Anser to Poll while already in reject mode. Needed for recovery of a lost REJ frame, expected when Timer T1 runs out
            #     self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'REJ', "Poll":True, "Payload": None, "Com": 'COM'})
            #     return None
        if self.transceiver.get_rej_active() and data["Poll"]:
            with self.transceiver.lock:
                self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'REJ', "Poll":True, "Payload": None, "Com": 'COM'})

        if self.transceiver.rej == "REJ":
            if not self.transceiver.get_rej_active():
            # if self.transceiver.rej_active != 1: # Don't resend REJ frame if already happend, or it will mess up the procedure
                self.transceiver.set_ns_before_seqbreak(data["Ns"])
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'REJ', "Poll":data["Poll"], "Payload": None, "Com":'COM'})
                self.transceiver.set_rej_active(1)

            return None
    
        elif self.transceiver.rej == "SREJ":
            return
        
        # Should never get here
        self.transceiver.logger.warning("Error in the recovery setup, neither REJ nor SREJ properly setup! Reverting to REJ as default!")
        self.transceiver.rej = "REJ"
        return None
    
    def __REJ_frame_handler(self, data):

        self.__acknowledgement_handler(data)

        # iters = 0
        # with self.transceiver.lock:
        self.transceiver.set_remote_busy(False)
            # if data["Com"] == 'COM' and data["Poll"] == True:
            #     self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RR', "Poll":True, "Payload": None, "Com": 'RES'}) #TODO: double check if this is really and RES frame. Not in doc but should be form my understanding

            # sendstate_at_rej = self.transceiver.get_state_variable('vs')
            # self.transceiver.send_state = data["Nr"]
        sendstate_at_rej = self.transceiver.get_state_variable('vs')
        self.transceiver.set_state_variable('vs', data["Nr"])
        self.transceiver.logger.debug(f"Offset, transceiver at: {sendstate_at_rej}, remote expected: {data['Nr']}")
            
            # while (data["Nr"] + iters)%self.transceiver.modulo != sendstate_at_rej: #TODO rework to for loop using range((end - start)%modulo)
            #     self.transceiver.framequeue.insert(iters, self.transceiver.frame_backlog[(data["Nr"]+iters)%self.transceiver.modulo])
            #     self.transceiver.logger.debug(f"Added frame from backlog pos {(data['Nr']+iters)%self.transceiver.modulo} to framequeue at pos {iters}")
            #     iters += 1

        for iters in range((sendstate_at_rej - data["Nr"])%self.transceiver.modulo):
            with self.transceiver.lock:
                self.transceiver.framequeue.insert(iters, self.transceiver.frame_backlog[(data["Nr"]+iters)%self.transceiver.modulo])
            self.transceiver.logger.debug(f"Added frame from backlog pos {(data['Nr']+iters)%self.transceiver.modulo} to framequeue at pos {iters}")

        return None
    
    def __SREJ_frame_handler(self, data):


        return None
    
    def __RR_frame_handler(self, data):
        
        # with self.transceiver.lock:
        self.transceiver.set_remote_busy(False)
            # if data["Nr"] != self.transceiver.ack_state: # Address this, as first frame has nr of 0 and will not change ack state
            #     self.transceiver.ack_state = data["Nr"]  # -> Should be fixed, V(a) is now equal to remotes V(r) and thus received N(r) 
            #                                             # -> First frame overall can't ack anything, so this is correct!

        self.__acknowledgement_handler(data)
                                                

        if data["Poll"] == True and self.transceiver.get_t1_try_count() == 0: #Answer to Poll coming from remote
            self.transceiver.logger.debug("Poll frame received, answering")
            # if self.transceiver.rej_active == 1:     
            #     self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'REJ', "Poll":True, "Payload": None, "Com": 'RES'})
            #     return
            if self.transceiver.get_state() == 'BUSY':
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RNR', "Poll":True, "Payload": None, "Com": 'RES'})
                return
            else:
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RR', "Poll":True, "Payload": None, "Com": 'RES'})
                return
            
        
        elif data["Poll"] == True and self.transceiver.get_t1_try_count() != 0: # final response to poll, act accrordingly
            
            # if self.transceiver.ack_state == self.transceiver.send_state: # No lost frames
            #     return
            self.transceiver.logger.debug("Final frame received, answering")
            if self.transceiver.get_state_variable("va") == self.transceiver.get_state_variable("vs"): # No lost frames
                return
            
            #Actual missing frames, retransmit. Same procedure as in __REJ_frame_handler
            sendstate_at_rej = self.transceiver.get_state_variable('vs')
            self.transceiver.set_state_variable('vs', data["Nr"])
            self.transceiver.logger.debug(f"Offset, transceiver at: {sendstate_at_rej}, remote expected: {data['Nr']}")
                
                # while (data["Nr"] + iters)%self.transceiver.modulo != sendstate_at_rej: #TODO rework to for loop using range((end - start)%modulo)
                #     self.transceiver.framequeue.insert(iters, self.transceiver.frame_backlog[(data["Nr"]+iters)%self.transceiver.modulo])
                #     self.transceiver.logger.debug(f"Added frame from backlog pos {(data['Nr']+iters)%self.transceiver.modulo} to framequeue at pos {iters}")
                #     iters += 1

            for iters in range((sendstate_at_rej - data["Nr"])%self.transceiver.modulo):
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(iters, self.transceiver.frame_backlog[(data["Nr"]+iters)%self.transceiver.modulo])
                self.transceiver.logger.debug(f"Added frame from backlog pos {(data['Nr']+iters)%self.transceiver.modulo} to framequeue at pos {iters}")
                    

        return
        

    
    def __RNR_frame_handler(self, data): #TODO T3 start/stop

        # with self.transceiver.lock:

        self.transceiver.set_remote_busy(True)

        self.__acknowledgement_handler(data)

            # if data["Nr"] != self.transceiver.ack_state: # Address this, as first frame has nr of 0 and will not change ack state
            #     self.transceiver.ack_state = data["Nr"]  # -> Should be fixed, V(a) is now equal to remotes V(r) and thus received N(r) 
            #                                             # -> First frame overall can't ack anything, so this is correct!
                                                    

        if data["Poll"] == True and self.transceiver.get_t1_try_count() == 0: #Answer to Poll coming from remote
            # if self.transceiver.rej_active == 1:     
            #     self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'REJ', "Poll":True, "Payload": None, "Com": 'RES'})
            #     return
            if self.transceiver.get_state() == 'BUSY':
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RNR', "Poll":True, "Payload": None, "Com": 'RES'})
                return
            else:
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(0, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type":'RR', "Poll":True, "Payload": None, "Com": 'RES'})
                return
            
        
        elif data["Poll"] == True and self.transceiver.get_t1_try_count() != 0: # final response to poll, act accrordingly
            
            # if self.transceiver.ack_state == self.transceiver.send_state: # No lost frames
            #     return

            if self.transceiver.get_state_variable("va") == self.transceiver.get_state_variable("vs"): # No lost frames
                return
            
            #Actual missing frames, retransmit. Same procedure as in __REJ_frame_handler
            sendstate_at_rej = self.transceiver.get_state_variable('vs')
            self.transceiver.set_state_variable('vs', data["Nr"])
            self.transceiver.logger.debug(f"Offset, transceiver at: {sendstate_at_rej}, remote expected: {data['Nr']}")
                
                # while (data["Nr"] + iters)%self.transceiver.modulo != sendstate_at_rej: #TODO rework to for loop using range((end - start)%modulo)
                #     self.transceiver.framequeue.insert(iters, self.transceiver.frame_backlog[(data["Nr"]+iters)%self.transceiver.modulo])
                #     self.transceiver.logger.debug(f"Added frame from backlog pos {(data['Nr']+iters)%self.transceiver.modulo} to framequeue at pos {iters}")
                #     iters += 1

            for iters in range((sendstate_at_rej - data["Nr"])%self.transceiver.modulo):
                with self.transceiver.lock:
                    self.transceiver.framequeue.insert(iters, self.transceiver.frame_backlog[(data["Nr"]+iters)%self.transceiver.modulo])
                self.transceiver.logger.debug(f"Added frame from backlog pos {(data['Nr']+iters)%self.transceiver.modulo} to framequeue at pos {iters}")
                
            return
        return


    def __acknowledgement_handler(self, data):

        # with self.transceiver.lock:
        if data["Nr"] == self.transceiver.get_state_variable("va"): return # No new frames have been acknolwedged, nothin to do
                
        if data["Nr"] == self.transceiver.get_state_variable("vs"): #All sent frames are acknowledged, stop timer t1
            self.transceiver.timer_cancel_t1.set()
        else: #Some new frames have been acknowledged, but not all, reset timer t1
            self.transceiver.timer_reset_t1.set()

        self.transceiver.set_state_variable("va", data["Nr"]) # = data["Nr"] # Update acknowledgement state variable

        return


            
                

        
