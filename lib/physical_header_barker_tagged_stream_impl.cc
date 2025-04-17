/* -*- c++ -*- */
/*
 * Copyright 2025 Julian Birk.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include <iterator>
#include <algorithm>
#include <gnuradio/io_signature.h>
#include "physical_header_barker_tagged_stream_impl.h"

namespace gr {
  namespace hwu {

    using input_type = uint8_t;
    using output_type = uint8_t;
    physical_header_barker_tagged_stream::sptr
    physical_header_barker_tagged_stream::make(int barker_len, bool add_tail, const std::string& lengthtagname)
    {
      return gnuradio::make_block_sptr<physical_header_barker_tagged_stream_impl>(
        barker_len, add_tail, lengthtagname);
    }


    /*
     * The private constructor
     */
    physical_header_barker_tagged_stream_impl::physical_header_barker_tagged_stream_impl(int barker_len, bool add_tail, const std::string& lengthtagname)
      : gr::tagged_stream_block("physical_header_barker_tagged_stream",
              gr::io_signature::make(1 /* min inputs */, 1 /* max inputs */, sizeof(input_type)),
              gr::io_signature::make(1 /* min outputs */, 1 /*max outputs */, sizeof(output_type)), lengthtagname),
              add_tail(add_tail)
    {
      std::vector<uint8_t> barker = BARKER_CODES.at(barker_len);
      set_tag_propagation_policy(TPP_DONT);
    }

    /*
     * Our virtual destructor.
     */
    physical_header_barker_tagged_stream_impl::~physical_header_barker_tagged_stream_impl()
    {
    }

    int
    physical_header_barker_tagged_stream_impl::calculate_output_stream_length(const gr_vector_int &ninput_items)
    {
      // int noutput_items = 0;
      size_t added_items = add_tail ? 2*barker.size() : barker.size();
      return ninput_items[0] + static_cast<int>(added_items);
    }

    int
    physical_header_barker_tagged_stream_impl::work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
      {
      auto in = static_cast<const input_type*>(input_items[0]);
      auto out = static_cast<output_type*>(output_items[0]);
      size_t packet_len = ninput_items[0];
      int added_items = add_tail ? static_cast<int>(2*barker.size()) : static_cast<int>(barker.size());
      std::vector<uint8_t> mybarker = BARKER_CODES.at(11);
      std::copy(std::begin(mybarker), std::end(mybarker), std::ostream_iterator<uint8_t>(std::cout, " "));
      // std::cout << "Barker code to be selected" << *BARKER_CODES.at(11).data() << std::endl;
      // std::cout << "Size of Barker code selected: " << barker.size() << std::endl;
      // std::copy(std::begin(barker), std::end(barker), std::ostream_iterator<uint8_t>(std::cout, " "));

      // Actual work
      // TODO: review copy function and debug here! 
      std::copy(std::begin(barker), std::end(barker), out);
      std::copy(in, in+packet_len, out + static_cast<int>(barker.size()));
      if (add_tail) {
        std::copy(std::begin(barker), std::end(barker), out + static_cast<int>(barker.size()) + packet_len);
      }
      // std::cout << "number of added items: " << added_items << std::endl;
      // Propagate tags

      std::vector<tag_t> tags;
      get_tags_in_range(tags, 0, nitems_read(0), nitems_read(0) + packet_len);
      for(const auto &tag : tags) {
        // tag.offset -= nitems_read(0);
        // if (tag.key != pmt::string_to_symbol(this->lengthtagname)) {
        add_item_tag(0, nitems_written(0) + tag.offset -nitems_read(0), tag.key, tag.value);
        // }
      }
      // Tell runtime system how many output items we produced.
      return packet_len + added_items;
    }

  } /* namespace hwu */
} /* namespace gr */
