/* -*- c++ -*- */
/*
 * Copyright 2025 Julian Birk.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_HWU_PHYSICAL_HEADER_BARKER_TAGGED_STREAM_IMPL_H
#define INCLUDED_HWU_PHYSICAL_HEADER_BARKER_TAGGED_STREAM_IMPL_H

#include <gnuradio/hwu/physical_header_barker_tagged_stream.h>
#include <unordered_map>
#include <vector>

namespace gr {
  namespace hwu {

    class physical_header_barker_tagged_stream_impl : public physical_header_barker_tagged_stream
    {
     private:
     bool add_tail;
     std::vector<uint8_t> barker;
     const std::unordered_map<int, std::vector<uint8_t>> BARKER_CODES={
        {2, {2}},      //[1,0]
        {3, {6}},      //[1,1,0]
        {4, {13}},     //[1,1,0,1]
        {5, {29}},     //[1,1,1,0,1]
        {7, {114}},    //[1,1,1,0,0,1,0]
        {11, {7,18}},  //[1,1,1,0,0,0,1,0,0,1,0]
        {13, {31,53}}  //[1,1,1,1,1,0,0,1,1,0,1,0,1]
        };

      // Nothing to declare in this block.

     protected:
      int calculate_output_stream_length(const gr_vector_int &ninput_items);

     public:
      

      physical_header_barker_tagged_stream_impl(int barker_len, bool add_tail, const std::string& lengthtagname);
      ~physical_header_barker_tagged_stream_impl();

      // Where all the action really happens
      int work(
              int noutput_items,
              gr_vector_int &ninput_items,
              gr_vector_const_void_star &input_items,
              gr_vector_void_star &output_items
      );
    };

  } // namespace hwu
} // namespace gr

#endif /* INCLUDED_HWU_PHYSICAL_HEADER_BARKER_TAGGED_STREAM_IMPL_H */
