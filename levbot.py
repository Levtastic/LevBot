import asyncio
import modules

from collections import defaultdict
from itertools import chain
from discord import Client


class LevBot(Client):
    def __init__(self):
        super().__init__()

        self.max_message_len = 2000
        self.newline_search_len = 200
        self.space_search_len = 100

        self._event_handlers = defaultdict(list)

        modules.init(self)

    def register_event(self, event, coroutine):
        self._event_handlers[event].append(coroutine)

    def unregister_event(self, event, coroutine):
        self._event_handlers[event].remove(coroutine)

    def dispatch(self, event, *args, **kwargs):
        super().dispatch(event, *args, **kwargs)

        for handler in self._event_handlers['on_' + event]:
            asyncio.ensure_future(handler(*args, **kwargs))

    async def on_ready(self):
        print('Connected as {!s}'.format(self.user))

    async def send_message(self, destination, content=None, *args, **kwargs):
        if content and len(str(content)) > self.max_message_len:
            return await self._split_message(
                destination, str(content), *args, **kwargs
            )

        return await super().send_message(
            destination, content, *args, **kwargs
        )

    async def _split_message(self, destination, content, *args, **kwargs):
        clipped, remainder = self._get_split_pieces(content)

        message1 = await self.send_message(
            destination, clipped, *args, **kwargs
        )
        message2 = await self.send_message(
            destination, remainder, *args, **kwargs
        )

        return tuple(chain((message1, message2)))

    def _get_split_pieces(self, string):
        piece = string[:self.max_message_len]
        if '\n' in piece[-self.newline_search_len:]:
            piece = piece.rsplit('\n', 1)[0]

        elif ' ' in piece[-self.space_search_len:]:
            piece = piece.rsplit(' ', 1)[0]

        return piece, string[len(piece):]
