import os
import logging
import discord
import modules
import settings

from datetime import datetime


class LevBot(discord.Client):
    def __init__(self):
        super().__init__()

        self.db = modules.Database(self)
        self.commands = modules.Commands(self)

        modules.Twitch(self)
        modules.ConsoleInput(self)

    async def on_ready(self):
        print('Connected!')
        print('Username: "{!s}"'.format(self.user))
        print('Invite URL: "{}"'.format(
            discord.utils.oauth_url(self.user.id)
        ))

    async def on_message(self, message):
        await self.commands.handle_message(message)


def set_up_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    os.makedirs('logs', exist_ok=True)
    filename = 'logs/{}.log'.format(
        datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    )
    filehandler = logging.FileHandler(filename)
    filehandler.setLevel(logging.INFO)
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)

    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.ERROR)
    streamhandler.setFormatter(formatter)
    logger.addHandler(streamhandler)

if __name__ == '__main__':
    set_up_logging()

    bot = LevBot()
    bot.run(settings.bot_token)
