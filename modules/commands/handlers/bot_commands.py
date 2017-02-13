import discord

from collections import defaultdict
from modules import UserLevel


class BotCommands:
    def __init__(self, commands):
        self.bot = commands.bot
        self.register(commands)

    def register(self, commands):
        commands.register_handler(
            'list channels',
            self.cmd_list_channels,
            user_level=UserLevel.global_bot_admin
        )
        commands.register_handler(
            'list users',
            self.cmd_list_users,
            user_level=UserLevel.global_bot_admin
        )
        commands.register_handler(
            'invite',
            self.cmd_invite,
            user_level=UserLevel.user
        )

    async def cmd_list_channels(self, attributes, message):
        """Lists channels the bot can currently see

        Syntax: `list channels`
        or `list channels <name>`"""

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
        """Lists users the bot can currently see

        Syntax: `list users`
        or `list users <name>`"""

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

    async def cmd_invite(self, attributes, message):
        await self.bot.send_message(
            message.author,
            'Use this invite link to add me to your server: {}'.format(
                discord.utils.oauth_url(self.bot.user.id)
            )
        )
