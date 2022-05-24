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
import trading_backend

import octobot_commons.logging as logging
import octobot_commons.constants as common_constants
import octobot_commons.enums as common_enums
import octobot_commons.tentacles_management as tentacles_management

import octobot_tentacles_manager.api as api

import octobot_trading.enums as enums
import octobot_trading.exchanges.types as exchanges_types
import octobot_trading.exchanges.exchange_manager as exchange_manager
import octobot_trading.exchanges.exchange_factory as exchange_factory


def get_margin_exchange_class(exchange_name, tentacles_setup_config):
    return search_exchange_class_from_exchange_name(exchanges_types.MarginExchange, exchange_name,
                                                    tentacles_setup_config)


def get_future_exchange_class(exchange_name, tentacles_setup_config):
    return search_exchange_class_from_exchange_name(exchanges_types.FutureExchange, exchange_name,
                                                    tentacles_setup_config)


def get_spot_exchange_class(exchange_name, tentacles_setup_config):
    return search_exchange_class_from_exchange_name(exchanges_types.SpotExchange, exchange_name,
                                                    tentacles_setup_config)


def search_exchange_class_from_exchange_name(exchange_class, exchange_name,
                                             tentacles_setup_config, enable_default=False):
    exchange_class = get_exchange_class_from_name(exchange_class, exchange_name,  tentacles_setup_config, enable_default)
    if exchange_class is not None:
        return exchange_class
    if enable_default:
        return None

    logging.get_logger().debug(f"No specific exchange implementation for {exchange_name} found, using a default one.")
    # TODO: handle default future exchange instead of creating a SpotExchange
    return search_exchange_class_from_exchange_name(exchanges_types.SpotExchange, exchange_name,
                                                    tentacles_setup_config, enable_default=True)


def get_exchange_class_from_name(exchange_parent_class, exchange_name, tentacles_setup_config, enable_default,
                                 strict_name_matching=False):
    for exchange_candidate in tentacles_management.get_all_classes_from_parent(exchange_parent_class):
        try:
            if _is_exchange_candidate_matching(exchange_candidate, exchange_name,
                                               tentacles_setup_config, enable_default=enable_default) and \
               (not strict_name_matching or exchange_candidate.get_name() == exchange_name):
                return exchange_candidate
        except NotImplementedError:
            # A subclass of AbstractExchange will raise a NotImplementedError when calling its get_name() method
            # Here we are returning only a subclass that matches the expected name
            # Only Exchange Tentacles are implementing get_name() to specify the related exchange
            # As we are searching for an exchange_type specific subclass
            # We should ignore classes that raises NotImplementedError
            pass
    return None


def _is_exchange_candidate_matching(exchange_candidate, exchange_name, tentacles_setup_config, enable_default=False):
    return not exchange_candidate.is_simulated_exchange() and \
           (not exchange_candidate.is_default_exchange() or enable_default) and \
           exchange_candidate.is_supporting_exchange(exchange_name) and \
           (tentacles_setup_config is None or
            api.is_tentacle_activated_in_tentacles_setup_config(tentacles_setup_config,
                                                                exchange_candidate.__name__))


def get_order_side(order_type):
    return enums.TradeOrderSide.BUY.value if order_type in (enums.TraderOrderType.BUY_LIMIT,
                                                            enums.TraderOrderType.BUY_MARKET) \
        else enums.TradeOrderSide.SELL.value


def log_time_sync_error(logger, exchange_name, error, details):
    logger.error(
        f"{_get_time_sync_error_message(exchange_name, details)} Error: {error}")


def _get_docs_url():
    try:
        import octobot.constants
        return octobot.constants.OCTOBOT_DOCS_URL
    except ImportError:
        return "https://docs.octobot.online"


def _get_exchanges_docs_url():
    try:
        import octobot.constants
        return octobot.constants.EXCHANGES_DOCS_URL
    except ImportError:
        return "https://exchanges.docs.octobot.online"


def _get_time_sync_error_message(exchange_name, details):
    return f"Time synchronization error when loading your {exchange_name.capitalize()} {details}. " \
        f"To fix this, please synchronize your computer's clock. See " \
        f"{_get_docs_url()}/installation/installation-troubleshoot#time-synchronization"


def get_partners_explanation_message():
    return f"More info on partner exchanges on {_get_exchanges_docs_url()}#partner-exchanges-support-octobot"


def _get_minimal_exchange_config(exchange_name, exchange_config):
    return {
        common_constants.CONFIG_EXCHANGES: {
            exchange_name: exchange_config
        },
        common_constants.CONFIG_TRADER: {
            common_constants.CONFIG_ENABLED_OPTION: False
        },
        common_constants.CONFIG_SIMULATOR: {
            common_constants.CONFIG_ENABLED_OPTION: False
        }
    }


async def is_compatible_account(exchange_name: str, exchange_config: dict, tentacles_setup_config) -> (bool, str):
    local_exchange_manager = exchange_manager.ExchangeManager(
        _get_minimal_exchange_config(exchange_name, exchange_config),
        exchange_name
    )
    local_exchange_manager.tentacles_setup_config = tentacles_setup_config
    # Avoid exchange authentication error log
    local_exchange_manager.is_collecting = True
    await exchange_factory.search_and_create_spot_exchange(local_exchange_manager)
    backend = trading_backend.exchange_factory.create_exchange_backend(local_exchange_manager.exchange)
    try:
        is_compatible, error = await backend.is_valid_account()
        message = f"[REST API] {exchange_name.capitalize()} connection can be faster " \
                  f"using websockets. {error}. " \
                  f"Please create a new {exchange_name.capitalize()} account to use websockets. "
        return is_compatible, message if error else error
    except trading_backend.TimeSyncError:
        return False, _get_time_sync_error_message(exchange_name, "account details")
    except trading_backend.ExchangeAuthError:
        return False, f"Invalid {exchange_name.capitalize()} authentication details"
    except Exception as e:
        return False, f"Error when loading exchange account: {e}"
    finally:
        # do not log stopping message
        local_exchange_manager.exchange.connector.logger.disable(True)
        await local_exchange_manager.exchange.stop()
        local_exchange_manager.exchange.connector.logger.disable(False)


async def get_historical_ohlcv(local_exchange_manager, symbol, time_frame, start_time, end_time):
    """
    Async generator, use as follows:
        async for candles in get_historical_ohlcv(exchange_manager, pair, time_frame, start_time, end_time):
            # candles stuff
    """
    reached_max = False
    while start_time < end_time and not reached_max:
        candles = await local_exchange_manager.exchange.get_symbol_prices(symbol, time_frame, since=int(start_time))
        if candles:
            start_time = candles[-1][common_enums.PriceIndexes.IND_PRICE_TIME.value]
            while start_time > end_time and candles:
                start_time = candles.pop(-1)[common_enums.PriceIndexes.IND_PRICE_TIME.value]
                reached_max = True
            if candles:
                local_exchange_manager.exchange.uniformize_candles_if_necessary(candles)
                yield candles
                # avoid fetching the last element twice
                start_time += 1
            else:
                reached_max = True
        else:
            reached_max = True


def get_exchange_type(exchange_manager_instance):
    if exchange_manager_instance.is_spot_only:
        return enums.ExchangeTypes.SPOT
    if exchange_manager_instance.is_future:
        return enums.ExchangeTypes.FUTURE
    if exchange_manager_instance.is_margin:
        return enums.ExchangeTypes.MARGIN
    return enums.ExchangeTypes.SPOT
