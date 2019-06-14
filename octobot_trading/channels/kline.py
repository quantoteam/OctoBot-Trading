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
from asyncio import CancelledError, Queue

from octobot_channels import CHANNEL_WILDCARD, CONSUMER_CALLBACK_TYPE
from octobot_commons.logging.logging_util import get_logger

from octobot_trading.channels.exchange_channel import ExchangeChannel
from octobot_channels.consumer import Consumer
from octobot_channels.producer import Producer


class KlineProducer(Producer):
    def __init__(self, channel):
        self.logger = get_logger(self.__class__.__name__)
        super().__init__(channel)

    async def push(self, time_frame, symbol, kline, reset=False):
        await self.perform(symbol, time_frame, kline, reset=reset)

    async def perform(self, time_frame, symbol, kline, reset=False):
        try:
            if (CHANNEL_WILDCARD in self.channel.consumers and self.channel.consumers[CHANNEL_WILDCARD]) or \
                    (symbol in self.channel.consumers or time_frame in self.channel.consumers[symbol]):
                if not reset:
                    await self.channel.exchange_manager.get_symbol_data(symbol).handle_kline_update(time_frame, kline)
                    await self.send(time_frame, symbol, kline)
                    await self.send(time_frame, symbol, kline, True)
                else:
                    await self.channel.exchange_manager.get_symbol_data(symbol).handle_kline_update(time_frame, kline)
        except CancelledError:
            self.logger.info("Update tasks cancelled.")
        except Exception as e:
            self.logger.error(f"exception when triggering update: {e}")
            self.logger.exception(e)

    async def send(self, time_frame, symbol, kline, is_wildcard=False):
        for consumer in self.channel.get_consumers_by_timeframe(symbol=CHANNEL_WILDCARD if is_wildcard else symbol,
                                                                time_frame=time_frame):
            await consumer.queue.put({
                "symbol": symbol,
                "time_frame": time_frame,
                "kline": kline
            })


class KlineConsumer(Consumer):
    def __init__(self, callback: CONSUMER_CALLBACK_TYPE, size=0):  # TODO REMOVE
        super().__init__(callback)
        self.filter_size = 0
        self.should_stop = False
        self.queue = Queue()
        self.callback = callback

    async def consume(self):
        while not self.should_stop:
            try:
                data = await self.queue.get()
                await self.callback(symbol=data["symbol"], time_frame=data["time_frame"], kline=data["kline"])
            except Exception as e:
                self.logger.exception(f"Exception when calling callback : {e}")


class KlineChannel(ExchangeChannel):
    def new_consumer(self, callback: CONSUMER_CALLBACK_TYPE, size: int = 0, symbol: str = CHANNEL_WILDCARD,
                     time_frame=None):
        self._add_new_consumer_and_run(KlineConsumer(callback, size=size), symbol=symbol, with_time_frame=True)
