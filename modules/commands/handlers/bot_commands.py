import discord

from collections import defaultdict
from modules import commands


class BotCommands:
    def __init__(self, commands):
        self.bot = commands.bot
        self.register(commands)

    def register(self, commands):
        commands.register_handler(self.cmd_list_channels, 'list channels')
        commands.register_handler(self.cmd_list_users, 'list users')

    async def cmd_list_channels(self, attributes, message):
        channels = defaultdict(list)

        for server, channel in self.get_text_channels(attributes):
            channels[server].append(channel)

        await self.bot.send_message(
            message.channel,
            self.get_channels_text(channels)
        )

    def get_text_channels(self, channel_filter):
        for server in self.bot.servers:
            for channel in server.channels:
                if channel.type != discord.ChannelType.text:
                    continue

                if channel_filter.lower() not in channel.name.lower():
                    continue

                yield server, channel

    def get_channels_text(self, channels):
        if not channels:
            return 'No channels found'

        return '.\n{}'.format('\n'.join(self.get_channels_text_pieces(channels)))

    def get_channels_text_pieces(self, channels):
        for server in channels.keys():
            yield 'Server: `{}`'.format(server)

            for channel in channels[server]:
                channel_text = '    `{0.id}`: `{0.name}`'.format(channel)

                if not channel.permissions_for(server.me).send_messages:
                    channel_text += ' (cannot message)'

                yield channel_text

    async def cmd_list_users(self, attributes, message):
        members = defaultdict(list)

        for server, member in self.get_members(attributes):
            members[server].append(member)

        await self.bot.send_message(
            message.channel,
            self.get_users_text(members)
        )

    def get_members(self, user_filter):
        for server in self.bot.servers:
            for member in server.members:
                if user_filter.lower() not in member.name.lower():
                    continue

                yield server, member

    def get_users_text(self, members):
        if not members:
            return 'No users found'

        return '.\n{}'.format('\n'.join(self.get_users_text_pieces(members)))

    def get_users_text_pieces(self, members):
        for server in members.keys():
            yield 'Server: `{}`'.format(server)

            for member in members[server]:
                member_text = '    `{0.id}`: `{0.name}`'.format(member)

                if member.nick:
                    member_text += ' `({0.nick})`'.format(member)

                if member.bot:
                    member_text += ' `BOT`'

                yield member_text
