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
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
import octobot_trading.enums as trading_enums
import octobot_trading.constants as trading_constants


def get_signal_exchange_type(exchange_manager):
    if exchange_manager.is_spot_only:
        return trading_enums.TradingSignalExchangeTypes.SPOT
    if exchange_manager.is_future:
        return trading_enums.TradingSignalExchangeTypes.FUTURE
    if exchange_manager.is_margin:
        return trading_enums.TradingSignalExchangeTypes.MARGIN
    return trading_enums.TradingSignalExchangeTypes.UNKNOWN


def create_order_signal_description(
        order, action,
        updated_quantity=trading_constants.ZERO,
        updated_limit_price=trading_constants.ZERO,
        updated_stop_price=trading_constants.ZERO,
        updated_current_price=trading_constants.ZERO,
    ):
    # prevent circular import
    import octobot_trading.personal_data as personal_data
    return {
        trading_enums.TradingSignalOrdersAttrs.ACTION.value: action.value,
        trading_enums.TradingSignalOrdersAttrs.SIDE.value: order.side.value,
        trading_enums.TradingSignalOrdersAttrs.TYPE.value:
            personal_data.get_order_type_from_class(order.__class__).value,
        trading_enums.TradingSignalOrdersAttrs.QUANTITY.value: float(order.origin_quantity),
        trading_enums.TradingSignalOrdersAttrs.UPDATED_QUANTITY.value: float(updated_quantity),
        trading_enums.TradingSignalOrdersAttrs.LIMIT_PRICE.value: float(order.origin_price),
        trading_enums.TradingSignalOrdersAttrs.UPDATED_LIMIT_PRICE.value: float(updated_limit_price),
        trading_enums.TradingSignalOrdersAttrs.STOP_PRICE.value: float(order.origin_stop_price),
        trading_enums.TradingSignalOrdersAttrs.UPDATED_STOP_PRICE.value: float(updated_stop_price),
        trading_enums.TradingSignalOrdersAttrs.CURRENT_PRICE.value: float(order.created_last_price),
        trading_enums.TradingSignalOrdersAttrs.UPDATED_CURRENT_PRICE.value: float(updated_current_price),
        trading_enums.TradingSignalOrdersAttrs.REDUCE_ONLY.value: order.reduce_only,
        trading_enums.TradingSignalOrdersAttrs.POST_ONLY.value: False,
        trading_enums.TradingSignalOrdersAttrs.GROUP_ID.value:
            None if order.order_group is None else order.order_group.name,
        trading_enums.TradingSignalOrdersAttrs.GROUP_TYPE.value:
            None if order.order_group is None else order.order_group.__class__.__name__,
        trading_enums.TradingSignalOrdersAttrs.TAG.value: order.tag,
        trading_enums.TradingSignalOrdersAttrs.SHARED_SIGNAL_ORDER_ID.value: order.shared_signal_order_id,
        trading_enums.TradingSignalOrdersAttrs.BUNDLED_WITH.value:
            None if order.triggered_by is None else order.triggered_by.shared_signal_order_id
        if order.has_been_bundled else None,
        trading_enums.TradingSignalOrdersAttrs.CHAINED_TO.value:
            None if order.triggered_by is None else order.triggered_by.shared_signal_order_id,
    }
