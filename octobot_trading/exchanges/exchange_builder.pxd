# cython: language_level=3
#  Drakkar-Software OctoBot-Trading
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
cimport octobot_trading.exchanges as exchanges

cdef class ExchangeBuilder:
    cdef object logger
    cdef public exchanges.ExchangeManager exchange_manager

    cdef dict config

    cdef bint _is_using_trading_modes

    cdef public str exchange_name
    cdef str _matrix_id

    """
    Builder methods
    """
    cpdef ExchangeBuilder is_backtesting(self, object backtesting_instance)
    cpdef ExchangeBuilder is_sandboxed(self, bint sandboxed)
    cpdef ExchangeBuilder is_simulated(self)
    cpdef ExchangeBuilder is_loading_markets(self, bint is_loading_markets)
    cpdef ExchangeBuilder is_real(self)
    cpdef ExchangeBuilder is_using_exchange_type(self, str exchange_type)
    cpdef ExchangeBuilder is_margin(self, bint use_margin=*)
    cpdef ExchangeBuilder is_exchange_only(self)
    cpdef ExchangeBuilder is_ignoring_config(self)
    cpdef ExchangeBuilder is_without_auth(self)
    cpdef ExchangeBuilder is_checking_credentials(self, bint check_credentials)
    cpdef ExchangeBuilder use_tentacles_setup_config(self, object tentacles_setup_config)
    cpdef ExchangeBuilder set_bot_id(self, str bot_id)
    cpdef ExchangeBuilder disable_trading_mode(self)
    cpdef ExchangeBuilder has_matrix(self, str matrix_id)

    cdef void _register_trading_modes_requirements(self, object trading_mode_class, object tentacles_setup_config)
    cdef object _ensure_exchange_compatibility(self)
    cdef object _ensure_trading_mode_compatibility(self, object trading_mode_class)

cpdef ExchangeBuilder create_exchange_builder_instance(object config, str exchange_name)
