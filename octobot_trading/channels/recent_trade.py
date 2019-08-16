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
from asyncio import CancelledError

from octobot_channels import CHANNEL_WILDCARD
from octobot_channels.producer import Producer

from octobot_trading.channels.exchange_channel import ExchangeChannel, ExchangeChannelProducer, ExchangeChannelConsumer


class RecentTradeProducer(ExchangeChannelProducer):
    def __init__(self, channel):  # TODO remove
        super().__init__(channel)
        self.channel = channel

    async def push(self, symbol, recent_trades, replace_all=False, partial=False):
        await self.perform(symbol, recent_trades, replace_all=replace_all, partial=partial)

    async def perform(self, symbol, recent_trades, replace_all=False, partial=False):
        try:
            if self.channel.get_consumers(symbol=CHANNEL_WILDCARD) or self.channel.get_consumers(symbol=symbol):
                recent_trades = self.channel.exchange_manager.get_symbol_data(symbol).handle_recent_trade_update(
                    recent_trades,
                    replace_all=replace_all,
                    partial=partial)

                if recent_trades:
                    await self.send_with_wildcard(symbol=symbol, recent_trades=recent_trades)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.error(f"exception when triggering update: {e}")
            self.logger.exception(e)

    async def send(self, symbol, recent_trades, is_wildcard=False):
        for consumer in self.channel.get_consumers(symbol=CHANNEL_WILDCARD if is_wildcard else symbol):
            await consumer.queue.put({
                "exchange": self.channel.exchange_manager.exchange.name,
                "symbol": symbol,
                "recent_trades": recent_trades
            })


class RecentTradeChannel(ExchangeChannel):
    FILTER_SIZE = 10
    PRODUCER_CLASS = RecentTradeProducer
    CONSUMER_CLASS = ExchangeChannelConsumer
