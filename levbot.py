import os
import logging
import discord
import modules
import settings

from datetime import datetime


class LevBot(discord.Client):
    def __init__(self):
        super().__init__()
        self.db = modules.Database()
        self.twitch = modules.Twitch(self)
        self.commands = modules.Commands(self)
        self.ci = modules.ConsoleInput(self)

    async def on_ready(self):
        print('Connected!')
        print('Username: {0.name}#{0.discriminator}'.format(self.user))
        print('Invite URL: https://discordapp.com/oauth2/authorize?&client_id={}&scope=bot&permissions=0'.format(self.user.id))

    async def on_message(self, message):
        command = self.get_command(message)

        if command and self.is_admin(message.author):
            await self.commands.do_command(command, message)

    def get_command(self, message):
        prefixes = (
            '<@{.id}>'.format(self.user), # standard mention
            '<@!{.id}>'.format(self.user) # nicknamed mention
        )

        for prefix in prefixes:
            if message.content.startswith(prefix):
                return message.content[len(prefix):].lstrip()

        if message.channel.is_private:
            return message.content

        return ''

    def is_admin(self, member):
        author_username = '{0.name}#{0.discriminator}'.format(member)
        if author_username in settings.admin_usernames:
            return True

        if self.db.admin_exists(member.id):
            return True

        return False


def set_up_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    os.makedirs('logs', exist_ok=True)
    filename = 'logs/{}.log'.format(datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
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
