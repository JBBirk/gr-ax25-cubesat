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

from concurrent.futures import thread
import bitstring as bs
import crc
import time
# from .ax25_transceiver import Transceiver
from .ax25_constants import *

class Framer:

    flag = bs.Bits(bin='0b01111110', length=8)

    def __init__(self, transceiver) -> None:
        self.transceiver = transceiver
        self.crc_calculator = crc.Calculator(crc.Crc16.KERMIT)



    """
    Used to build the bitstructure of the frame object

    @return: bytes bitframe
    """
    
    def frame(self, frametype:str, src_addr:str, src_ssid:int , dest_addr:str, dest_ssid:int, pid:bs.Bits, payload:bytes, command_response:str, modulo=8, poll_final=False):

        # start_time = time.time()
        """ Turn source address to bits """
        local_src = bs.BitArray()
        while(len(src_addr) < 6):
            src_addr = src_addr + " "
        for letter in src_addr:
             local_src += bs.BitArray(int=ord(letter), length=8)

        """ Turn source ssid to bits, with command/responce ecoding """
        if command_response == 'COM':
            local_src += bs.Bits(bin='0b011', length=3) + bs.Bits(int=src_ssid, length=4) + bs.Bits(bin='0b1', length=1)
        if command_response == 'RES':
            local_src += bs.Bits(bin='0b111', length=3) + bs.Bits(int=src_ssid, length=4) + bs.Bits(bin='0b1', length=1)
        

        """ Turn destination address to bits """
        local_dest = bs.BitArray()
        while(len(dest_addr) < 6):
            dest_addr = dest_addr + " "
        for letter in dest_addr:
            local_dest += bs.BitArray(int=ord(letter), length=8) 


        """ Turn destination ssid to bits, with command/responce ecoding """
        if command_response == 'COM':
            local_dest += bs.Bits(bin='0b111', length=3) + bs.Bits(int=dest_ssid, length=4) + bs.Bits(bin='0b0', length=1)
        if command_response == 'RES':
            local_dest += bs.Bits(bin='0b011', length=3) + bs.Bits(int=dest_ssid, length=4) + bs.Bits(bin='0b0', length=1)

        # self.transceiver.logger.debug(f"Preparation took: {round((time.time() - start_time)*1000)} ms")

        """ Call appropriate framing subfunction """

        if frametype == 'I':

            return self.__build_I_frame(local_src, local_dest, pid, payload, poll_final)
            
        if frametype in S_FRAMES:

            return self.__build_S_frame(local_src, local_dest, frametype, poll_final)
                
        if frametype in U_FRAMES:
            
            return self.__build_U_frame(local_src, local_dest, frametype, payload, poll_final)      

        self.transceiver.logger.warning("Non-existend framtype provided for framing!")


    """ Private function that builds I frames """

    def __build_I_frame(self, src:bs.Bits, dest:bs.Bits, pid:bs.Bits, payload:bytes, poll_final:bool=False):

        start_time = time.time()

        if self.transceiver.modulo == 8:
            """ Peprare control field """
            # lock_time = time.time() - start_time
            c_field = bs.BitArray(uint=self.transceiver.get_state_variable("vr"), length=3) + bs.BitArray(bool=poll_final) + bs.BitArray(uint=self.transceiver.get_state_variable("vs"), length=3) + bs.BitArray(int=0, length=1)
            
            # c_field_time = time.time() - start_time - lock_time
            """ Turn payload into bits and perform crc calculation"""

            
            info = bs.BitArray(bytes=payload)
            fcs = bs.BitArray(uint=self.calc_checksum(dest.bytes + src.bytes + c_field.bytes + pid.bytes + info.bytes), length=16)
            # checksum_time = time.time() - start_time - c_field_time - lock_time

            """ Form Frame """
            bitframe = bs.BitArray()
            bitframe = self.flag.tobitarray() #Doesn't need mirror for LSB, because it symmetrical
            bitframe += dest
            bitframe += src
            bitframe += c_field
            bitframe += pid
            bitframe += info
            bitframe += fcs
            # Change/Add things here for bigger payloads (e.g. files), so the flag isn't sent twice
            bitframe += self.flag.bytes
            
            # forming_time = time.time() - start_time - c_field_time - checksum_time - lock_time

            """ Mirror bitorder per byte to get LSB first (when reading from left to right) """
            for position in range(8, len(bitframe)-24, 8): # Start after flag and stop before fcs field
                currentbyte = bitframe[position:position+8]
                bitframe[position:position+8] = currentbyte[::-1]

            # lsb_time = time.time()- start_time - c_field_time - checksum_time - forming_time - lock_time

            # Perform bitstuffing 
            bitframe.replace('0b11111', '0b111110', 8, -8)

            current_send_state = self.transceiver.get_state_variable("vs")

            with self.transceiver.lock:
                # lock_time_stuffing = time.time() - start_time - c_field_time - checksum_time - forming_time - lsb_time - lock_time
                self.transceiver.frame_backlog.insert(current_send_state, {"Dest":[self.transceiver.dest_addr, self.transceiver.dest_ssid], "Type": 'I', "Poll": poll_final, "Payload": payload, "Com": 'COM'})

            self.transceiver.set_state_variable("vs", ((current_send_state + 1)%self.transceiver.modulo))

            # stuffing_time = time.time() - start_time - c_field_time - checksum_time - forming_time - lsb_time - lock_time_stuffing - lock_time
              
            return bitframe
        

    """ Private function that builds S frames """

    def __build_S_frame(self, src, dest, frametype, poll_final=False):

        """ Prepare control field """
        c_field = bs.BitArray(uint=self.transceiver.get_state_variable("vr"), length=3) + bs.BitArray(bool=poll_final) + bs.BitArray(bin=S_FRAMES[frametype])

        """ Calculate CRC"""

        fcs = bs.BitArray(uint=self.calc_checksum(dest.bytes + src.bytes + c_field.bytes), length=16)

        """ Form Frame"""
        bitframe = self.flag.bytes #Doesn't need mirror for LSB, because it symmetrical
        bitframe += dest
        bitframe += src
        bitframe += c_field
        bitframe += fcs
        # Change/Add things here for bigger payloads (e.g. files), so the flag isn't sent twice
        bitframe += self.flag.bytes

        """ Mirror bitorder per byte to get LSB first (when reading from left to right) """
        for position in range(8, len(bitframe)-24, 8): # Start after flag and stop before fcs field
            currentbyte = bitframe[position:position+8]
            bitframe[position:position+8] = currentbyte[::-1]

        bitframe.replace('0b11111', '0b111110', 8, -8)

        return bitframe

    """ Private function that builds U frames """

    def __build_U_frame(self, src, dest, frametype, payload=None, poll_final=False):

        """ Prepare control field """
        c_field = bs.BitArray(bin=U_FRAMES[frametype][0]) + bs.BitArray(bool=poll_final) + bs.BitArray(bin=U_FRAMES[frametype][1])
        """ Turn payload into bits, calc checksum and form frame if payload exist"""
        if payload is not None:
            
            info = bs.BitArray(bytes=payload)
            fcs = bs.BitArray(uint=self.calc_checksum(dest.bytes + src.bytes + c_field.bytes + info.bytes), length=16)

            bitframe = self.flag.bytes #Doesn't need mirror for LSB, because it symmetrical
            bitframe += dest
            bitframe += src
            bitframe += c_field
            bitframe += info
            bitframe += fcs
            # Change/Add things here for bigger payloads (e.g. files), so the flag isn't sent twice
            bitframe += self.flag.bytes
        
        else: 

            fcs = bs.BitArray(uint=self.calc_checksum(dest.bytes + src.bytes + c_field.bytes), length=16)

            bitframe = self.flag.bytes #Doesn't need mirror for LSB, because it symmetrical
            bitframe += dest
            bitframe += src
            bitframe += c_field
            bitframe += fcs
            # Change/Add things here for bigger payloads (e.g. files), so the flag isn't sent twice
            bitframe += self.flag.bytes

        """ Mirror bitorder per byte to get LSB first (when reading from left to right) """
        for position in range(8, len(bitframe)-24, 8): # Start after flag and stop before fcs field
            currentbyte = bitframe[position:position+8]
            bitframe[position:position+8] = currentbyte[::-1]
        
        bitframe.replace('0b11111', '0b111110', 8, -8)

        return bitframe


    """ Used to deframe an incoming frame and retreive information 

        @return: dict [Type, Poll, Pid-Data, Nr, Ns, Com]
    """
    def deframe(self, bitframe:bs.BitArray):

        """ Check for 0 length frame reception """
        if bitframe.len == 0:
            self.transceiver.logger.debug("Zero bit frame received")
            return {"Type": 'ERROR', "Poll": False, "Pid-Data": None, "Nr": None, "Ns":None, "Com": None}

        """ Check if frame is octet aligned """
        if bitframe.len % 8 != 0:
            self.transceiver.logger.debug(f"Frame not octet aligned: mod {bitframe.len % 8}")
            return {"Type": 'ERROR', "Poll": False, "Pid-Data": None, "Nr": None, "Ns":None, "Com": None}
        
        """ Undo LSB order """
        for position in range(0, len(bitframe)-16, 8): #Start at first bit, stop before fcs field. 0x7e flag has already been taken off
            currentbyte = bitframe[position:position+8]
            bitframe[position:position+8] = currentbyte[::-1]
        
        
        try:
            dest_addr, dest_ssid, src_addr, src_ssid, c_field, pid_and_info, fcs_field = bitframe.unpack('bits:48, bits:8, bits:48, bits:8, bits:8, bits, bits:16')
        except:
            self.transceiver.logger.warning("Unpacking frame failed")
            return {"Type": 'ERROR', "Poll": False, "Pid-Data": None, "Nr": None, "Ns":None, "Com": None}
        try:
            if dest_addr.tobytes().decode() != self.transceiver.src_addr: #or dest_ssid.uint != transceiver.src_ssid: Moved to before checksum, to filter out 
                self.transceiver.logger.debug("Frame Addresses some other receiver")
                return {"Type": 'ERROR', "Poll": False, "Pid-Data": None, "Nr": None, "Ns":None, "Com": None}
        except UnicodeDecodeError: #This means its idle data from the radio that can't be decoded
            return {"Type": 'ERROR', "Poll": False, "Pid-Data": None, "Nr": None, "Ns":None, "Com": None}


        fcs = self.calc_checksum(dest_addr.bytes + dest_ssid.bytes + src_addr.bytes + src_ssid.bytes + c_field.bytes + pid_and_info.bytes)
        if fcs != fcs_field.uint:
            self.transceiver.logger.debug(f"Error in CRC in frame: {dest_addr.hex + dest_ssid.hex + src_addr.hex + src_ssid.hex + c_field.hex + pid_and_info.hex}")
            self.transceiver.logger.debug(f"Full frame: {bitframe.hex}")
            self.transceiver.logger.debug(f"Sent CRC: {fcs_field.uint}, calculated: {fcs}")
            return {"Type": 'ERROR', "Poll": False, "Pid-Data": None, "Nr": None, "Ns":None, "Com": None}
        

        
        com = 'COM' if dest_ssid[0] == 1 and src_ssid[0] == 0 else 'RES'
            
        """ Extract control field data to return """
        if c_field[-1] == 0: # For an Information Frame

            nr, poll, ns, _ = c_field.unpack('uint:3, bool, uint:3, bool')
            if ns == self.transceiver.get_state_variable("vr"):
                frametype = "I"
                return {"Type": frametype, "Poll": poll, "Pid-Data": pid_and_info, "Nr": nr, "Ns":ns, "Com": com}
            
            else: 
                self.transceiver.logger.debug('Frame Sequence Error: n(s) = %d, v(r) = %d, n(r) = %d, v(s) = %d', ns, self.transceiver.get_state_variable("vr"), nr, self.transceiver.get_state_variable("vs"))
                frametype = "RECOVERY"
                return {"Type": frametype, "Poll": poll, "Pid-Data": pid_and_info, "Nr": nr, "Ns":ns, "Com": com}
            

        elif c_field[-1] == 1 and c_field[-2] == 0: # For a supervisory frame

            nr, poll, frametype_bits = c_field.unpack('uint:3, bool, bits:4')
            try:
                frametype = S_FRAMES_INVERSE[frametype_bits.bin]
            except:
                self.transceiver.logger.debug("Frametype Error, invalid c_field encoding")
                return {"Type": 'ERROR', "Poll": False, "Pid-Data": None, "Nr": None, "Ns":None, "Com": None}
                
            return {"Type": frametype, "Poll": poll, "Pid-Data": pid_and_info, "Nr": nr, "Ns":None, "Com": com}
        
        elif c_field[-1] == 1 and c_field[-2] == 1: # For an unnumbered frame

            frametype_bits1, poll, frametype_bits2 = c_field.unpack('bits:3, bool, bits:4')
            frametype_bits = frametype_bits1 + frametype_bits2

            try:
                frametype = U_FRAMES_INVERSE[frametype_bits.bin]
            except:
                self.transceiver.logger.debug("Frametype Error, incalid c_field encoding!")
                return {"Type": 'ERROR', "Poll": False, "Pid-Data": None, "Nr": None, "Ns":None, "Com": None}
            
            return {"Type": frametype, "Poll": poll, "Pid-Data": pid_and_info, "Nr": None, "Ns":None, "Com": com}

        #we should never get here
        self.transceiver.logger.debug("Something went wrong while decoding the c_field")
        return {"Type": 'ERROR', "Poll": False, "Pid-Data": None, "Nr": None, "Ns":None, "Com": None}
    
    """ Implementation of the checksum calculation
    
        @return: int checksum
    """
    def calc_checksum(self, data:bytes):
            return self.crc_calculator.checksum(data) & 0xFFFF # Effectively turns negative numbers back into positive, so int -> uint