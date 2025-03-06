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

""" Constants """
S_FRAMES = {'RR': '0b0001', #defines S_Frame subtypes and respective c-field encoding
            'RNR': '0b0101',
            'REJ': '0b1001',
            'SREJ': '0b1101'}
S_FRAMES_INVERSE = {'0001': 'RR',
                    '0101': 'RNR',
                    '1001': 'REJ',
                    '1101': 'SREJ'} 
U_FRAMES = {'SABME': ['0b011','0b1111'], #defines U-Frame subtypes and respective c-field encoding (which is split into forst and second part)
            'SABM': ['0b001','0b1111'],
            'DISC': ['0b010','0b0011'],
            'DM': ['0b000','0b1111'],
            'UA': ['0b011','0b0011'],
            'FRMR': ['0b100','0b0111'], #Outdate and not used in current versions, but kept just in case
            'UI': ['0b000','0b0011'],
            'XID': ['0b101','0b1111'],
            'TEST': ['0b111','0b0011']}
U_FRAMES_INVERSE =  {'0111111': 'SABME',
                     '0011111': 'SABM',
                     '0100011': 'DISC',
                     '0001111': 'DM',
                     '0110011': 'UA',
                     '1000111': 'FRMR',
                     '0000011': 'UI',
                     '1011111': 'XID',
                     '1110011': 'TEST'}

PID = '0xF0'
