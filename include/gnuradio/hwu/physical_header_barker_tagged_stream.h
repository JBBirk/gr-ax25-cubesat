/* -*- c++ -*- */
/*
 * Copyright 2025 Julian Birk.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_HWU_PHYSICAL_HEADER_BARKER_TAGGED_STREAM_H
#define INCLUDED_HWU_PHYSICAL_HEADER_BARKER_TAGGED_STREAM_H

#include <gnuradio/hwu/api.h>
#include <gnuradio/tagged_stream_block.h>

namespace gr {
  namespace hwu {

    /*!
     * \brief <+description of block+>
     * \ingroup hwu
     *
     */
    class HWU_API physical_header_barker_tagged_stream : virtual public gr::tagged_stream_block
    {
     public:
      typedef std::shared_ptr<physical_header_barker_tagged_stream> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of hwu::physical_header_barker_tagged_stream.
       *
       * To avoid accidental use of raw pointers, hwu::physical_header_barker_tagged_stream's
       * constructor is in a private implementation
       * class. hwu::physical_header_barker_tagged_stream::make is the public interface for
       * creating new instances.
       */
      static sptr make(int barker_len, bool add_tail, const std::string& lengthtagname);
    };

  } // namespace hwu
} // namespace gr

#endif /* INCLUDED_HWU_PHYSICAL_HEADER_BARKER_TAGGED_STREAM_H */
