import discord

from collections import defaultdict
from modules import commands


class BotCommands:
    def __init__(self, commands):
        self.bot = commands.bot
        self.register(commands)

    def register(self, commands):
        commands.register_handler(self._list_channels, 'list channels')
        commands.register_handler(self._list_users, 'list users')

    async def _list_channels(self, list_filter, message):
        channels = defaultdict(list)
        return_text = '.\n'

        for server in self.bot.servers:
            for channel in server.channels:
                if channel.type == discord.ChannelType.text:
                    if list_filter.lower() in channel.name.lower():
                        channels[server].append(channel)

        if not channels:
            return await self.bot.send_message(
                message.channel,
                'No channels found'
            )

        for server in channels.keys():
            return_text += 'Server: `{}`\n'.format(server)
            for channel in channels[server]:
                return_text += '    `{0.id}`: `{0.name}`'.format(channel)

                if not channel.permissions_for(server.me).send_messages:
                    return_text += ' (cannot message)'

                return_text += '\n'

        await self.bot.send_message(message.channel, return_text)

    async def _list_users(self, list_filter, message):
        users = defaultdict(list)
        return_text = '.\n'

        for server in self.bot.servers:
            for member in server.members:
                if list_filter.lower() in member.name.lower():
                    users[server].append(member)

        if not users:
            return await self.bot.send_message(
                message.channel,
                'No users found'
            )

        for server in users.keys():
            return_text += 'Server: `{}`\n'.format(server)
            for member in users[server]:
                return_text += '    `{0.id}`: `{0.name}`'.format(member)

                if member.nick:
                    return_text += ' `({0.nick})`'.format(member)

                if member.bot:
                    return_text += ' `BOT`'

                return_text += '\n'

        await self.bot.send_message(message.channel, return_text)
