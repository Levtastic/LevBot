import discord
import settings

from collections import defaultdict
from datetime import datetime
from discord import NotFound, Forbidden
from modules import UserLevel


class BotCommands:
    def __init__(self, commands):
        self.bot = commands.bot
        self.register(commands)

    def register(self, commands):
        commands.register_handler(
            'list all channels',
            self.cmd_list_all_channels,
            user_level=UserLevel.global_bot_admin,
            description=(
                'Lists channels the bot can currently see'
            )
        )
        commands.register_handler(
            'list all users',
            self.cmd_list_all_users,
            user_level=UserLevel.global_bot_admin,
            description=(
                'Lists users the bot can currently see'
            )
        )
        commands.register_handler(
            'invite',
            self.cmd_invite,
            user_level=UserLevel.user,
            description=(
                'Sends a link in private that can be used to invite the'
                ' bot to your server'
            )
        )
        commands.register_handler(
            'quit',
            self.cmd_quit,
            user_level=UserLevel.bot_owner,
            description=(
                'Immediately shuts down the bot'
            )
        )
        commands.register_handler(
            'say',
            self.cmd_say,
            user_level=UserLevel.server_bot_admin,
            description=(
                'Replies in the same location as the command, with the same'
                ' message content as the command (not including the word "say")'
            )
        )
        commands.register_handler(
            'sayd',
            self.cmd_sayd,
            user_level=UserLevel.server_bot_admin,
            description=(
                'Deletes the message containing the command and then replies in'
                ' the same location as the command, with the same message content'
                ' as the command (not including the word "sayd")\n'
                'This command does nothing if the bot doesn\'t have permission'
                ' to delete messages'
            )
        )
        commands.register_handler(
            'backup',
            self.cmd_backup,
            user_level=UserLevel.server_bot_admin,
            description=(
                'Replies in private with the current timestamp (in'
                ' international ISO format) and the current database file'
                ' attached. Changes to the database made in the last second'
                ' may not be reflected in the file, as they may not have'
                ' been committed yet.'
            )
        )

        if settings.source_url:
            commands.register_handler(
                'source',
                self.cmd_source,
                user_level=UserLevel.user,
                description=(
                    'Sends a link in private to view the bot source code'
                )
            )

        if settings.donate_url:
            commands.register_handler(
                'donate',
                self.cmd_donate,
                user_level=UserLevel.user,
                description=(
                    'If you want to buy my dad a drink, I\'ll send you a paypal'
                    ' donate link and you can tell him how much you appreciate me!'
                )
            )

    async def cmd_list_all_channels(self, message, channel_filter=''):
        channels = defaultdict(list)

        for server, channel in self.get_text_channels(channel_filter):
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

        return '\u200C\n{}'.format('\n'.join(self.get_channels_text_pieces(channels)))

    def get_channels_text_pieces(self, channels):
        for server in channels.keys():
            yield 'Server: `{}`'.format(server)

            for channel in channels[server]:
                channel_text = '    `{0.id}`: `{0.name}`'.format(channel)

                if not channel.permissions_for(server.me).send_messages:
                    channel_text += ' (cannot message)'

                yield channel_text

    async def cmd_list_all_users(self, message, user_filter=''):
        members = defaultdict(list)

        for server, member in self.get_members(user_filter):
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

        return '\u200C\n{}'.format('\n'.join(self.get_users_text_pieces(members)))

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

    async def cmd_invite(self, message):
        await self.bot.send_message(
            message.author,
            'Use this invite link to add me to your server: {}'.format(
                discord.utils.oauth_url(self.bot.user.id)
            )
        )

    async def cmd_quit(self, message):
        await self.bot.send_message(message.channel, 'Shutting down.')
        await self.bot.logout()

    async def cmd_say(self, message, text):
        await self.bot.send_message(message.channel, text)

    async def cmd_sayd(self, message, text):
        try:
            await self.bot.delete_message(message)
            await self.cmd_say(message, text)

        except (NotFound, Forbidden):
            pass

    async def cmd_backup(self, message):
        await self.bot.send_file(
            message.author,
            settings.db_name,
            content='BACKUP ' + datetime.now().isoformat(' ')
        )

    async def cmd_source(self, message):
        await self.bot.send_message(message.author, settings.source_url)

    async def cmd_donate(self, message):
        await self.bot.send_message(message.author, settings.donate_url + (
            '\n\n'
            "Donating isn't required to use me, but any money you want to send will"
            ' be very much appreciated by my dad who spent many months to make me,'
            ' and who still has to jump in and help me when I get confused by twitch'
            ' API changes.'
        ))
