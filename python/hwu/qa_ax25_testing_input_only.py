#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Julian Birk.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

from gnuradio import gr, gr_unittest, blocks, pdu
from gnuradio.hwu import ax25_testing_input_only
import bitstring as bs
import time

class qa_ax25_testing_input_only(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_instance(self):
        # FIXME: Test will fail until you pass sensible arguments to the constructor
        instance = ax25_testing_input_only('HWUGND', 1, 'HWUSAT', 1, True, 'SREJ', 8, 2048, 7, 3, 10)

    def test_001_generate_frame(self):

        #define data
        data_in = [1,2,3]
        #define blocks
        src = blocks.vector_source_b(data_in, False, 1, [])
        to_tagged = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, 3, "tx_pck_len")
        to_pdu = pdu.tagged_stream_to_pdu(gr.types.byte_t, "tx_pck_len")
        ax25_impl = ax25_testing_input_only('HWUGND', 1, 'HWUSAT', 1, True, 'SREJ', 8, 2048, 7, 3, 10)
        sink = blocks.message_debug()

        #set up connections
        self.tb.connect(src, to_tagged)
        self.tb.connect(to_tagged, to_pdu)
        self.tb.msg_connect(to_pdu, 'pdus', ax25_impl, 'Payload in')
        self.tb.msg_connect(ax25_impl, 'Frame out', sink, 'store')
        # set up fg
        self.tb.start()  
        time.sleep(5)    
        #check data
        print(f"[TEST]The number of messages received by the sink: {sink.num_messages()}")
        #print(sink.get_message(0))
    
    def test_srej(self):
        ax25_impl = ax25_testing_input_only('HWUGND', 1, 'HWUSAT', 1, True, 'SREJ', 8, 2048, 7, 3, 10)
        transceiver = ax25_impl.transceiver
        with transceiver.lock:
            transceiver.frame_backlog[0] = {"Dest":[transceiver.dest_addr, transceiver.dest_ssid],
                                "Type":'I', "Poll":False, "Payload": b'frame0', "Com":'COM', "Ns":0}
            transceiver.frame_backlog[1] = {"Dest":[transceiver.dest_addr, transceiver.dest_ssid],
                                "Type":'I', "Poll":False, "Payload": b'frame1', "Com":'COM', "Ns":1}
            transceiver.frame_backlog[2] = {"Dest":[transceiver.dest_addr, transceiver.dest_ssid],
                                "Type":'I', "Poll":False, "Payload": b'frame2', "Com":'COM', "Ns":2}
            transceiver.frame_backlog[3] = {"Dest":[transceiver.dest_addr, transceiver.dest_ssid],
                                "Type":'I', "Poll":False, "Payload": b'frame3', "Com":'COM', "Ns":3}

        #构造recovery_frame，触发SREJ
        recovery_frame = {
            "Type":'RECOVERY',
            "Poll":False,
            "Ns":3,
            "Nr":2,
            "Dest":[transceiver.dest_addr, transceiver.dest_ssid]
        }
        try:
            transceiver.downlinker.handler_functions['RECOVERY'](recovery_frame)
            print(f"[SREJ]SREJ activation tag(rej_active)：{transceiver.get_rej_active()}")
            print(f"[SREJ]Lost frame sequence number(ns_before_seqbreak)：{transceiver.get_ns_before_seqbreak()}")
            srej_num = 0
            with transceiver.lock:
                for f in transceiver.framequeue:
                    if f.get("Type") == "SREJ":
                        srej_num += 1
            print(f"[SREJ]The number of SREJ frame：{srej_num}")
        except Exception as e:
            print(f"[SREJ]触发SREJ异常：{e}")

        #构造SREJ帧，触发重传 + 模拟重传成功
        srej_frame = {
            "Type":'SREJ',
            "Nr":2,
            "Poll":False,
            "Dest":[transceiver.dest_addr, transceiver.dest_ssid]
        }
        try:
            transceiver.downlinker.handler_functions['SREJ'](srej_frame)
            with transceiver.lock:
                retrans_frame = transceiver.framequeue[0] if transceiver.framequeue else None
            if retrans_frame and retrans_frame.get("Ns") == 2:
                print(f"[SREJ]Success! The head of the queue is frame {retrans_frame.get('Ns')}")
            else:
                print(f"[SREJ]重传帧验证：失败！当前帧：{retrans_frame}")

            i_frame_2 = {
                "Type":'I',
                "Ns":2,
                "Nr":0,
                "Poll":False,
                "Pid-Data": bs.BitArray(b'frame2'),
                "Dest":[transceiver.dest_addr, transceiver.dest_ssid]
            }
            transceiver.downlinker.handler_functions['I'](i_frame_2)
            print(f"[SREJ]SREJ Recovery finished,rej_active={transceiver.get_rej_active()}")
        except Exception as e:
            print(f"[SREJ]SREJ重传/状态更新异常：{e}")

 

if __name__ == '__main__':
    gr_unittest.run(qa_ax25_testing_input_only)