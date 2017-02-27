import os
import logging
import asyncio
import discord
import modules
import settings

from datetime import datetime
from collections import defaultdict
from itertools import chain
from pushbulletlogging import PushbulletHandler


class LevBot(discord.Client):
    def __init__(self):
        super().__init__()

        self.max_message_len = 2000
        self.newline_search_len = 200

        self._event_handlers = defaultdict(list)

        self._load_modules()

    def _load_modules(self):
        for module in modules.to_init:
            module(self)

    def register_event(self, event, coroutine):
        self._event_handlers[event].append(coroutine)

    def unregister_event(self, event, coroutine):
        self._event_handlers[event].remove(coroutine)

    def dispatch(self, event, *args, **kwargs):
        super().dispatch(event, *args, **kwargs)

        for handler in self._event_handlers['on_' + event]:
            asyncio.ensure_future(handler(*args, **kwargs))

    async def on_ready(self):
        print('Connected!')
        print('Username: "{!s}"'.format(self.user))
        print('Invite URL: "{}"'.format(
            discord.utils.oauth_url(self.user.id)
        ))

    async def send_message(self, destination, content=None, *args, **kwargs):
        if content and len(str(content)) > self.max_message_len:
            return await self._split_message(destination, str(content), *args, **kwargs)

        return await super().send_message(destination, content, *args, **kwargs)

    async def _split_message(self, destination, content, *args, **kwargs):
        clipped, remainder = self._get_split_pieces(content)

        message1 = await self.send_message(destination, clipped, *args, **kwargs)
        message2 = await self.send_message(destination, remainder, *args, **kwargs)

        return tuple(chain((message1, message2)))

    def _get_split_pieces(self, string):
        piece = string[:self.max_message_len]
        if '\n' in piece[-self.newline_search_len:]:
            piece = piece.rsplit('\n', 1)[0]

        return piece, string[len(piece):]


def set_up_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    add_file_logger(logger, formatter)
    add_console_logger(logger, formatter)
    add_pushbullet_logger(logger, formatter)

def add_file_logger(logger, formatter):
    os.makedirs('logs', exist_ok=True)
    filename = 'logs/{}.log'.format(
        datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    )
    filehandler = logging.FileHandler(filename)
    filehandler.setLevel(logging.INFO)
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)

    return filehandler

def add_console_logger(logger, formatter):
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.ERROR)
    streamhandler.setFormatter(formatter)
    logger.addHandler(streamhandler)

    return streamhandler

def add_pushbullet_logger(logger, formatter):
    if not settings.pushbullet_token:
        return None

    pushbullethandler = PushbulletHandler(
        access_token=settings.pushbullet_token
    )
    pushbullethandler.setLevel(logging.ERROR)
    pushbullethandler.setFormatter(formatter)
    logger.addHandler(pushbullethandler)

    return pushbullethandler

def remove_pushbullet_logger():
    logger = logging.getLogger()
    logger.handlers = [h for h in logger.handlers if not isinstance(h, PushbulletHandler)]


if __name__ == '__main__':
    set_up_logging()

    bot = LevBot()
    bot.run(settings.bot_token)

    remove_pushbullet_logger()
