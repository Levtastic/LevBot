import discord
import re

from modules import database
from modules import UserLevel
from .. import CommandException


class AlertCommands:
    def __init__(self, commands):
        self.user_level = UserLevel.server_bot_admin

        self.bot = commands.bot
        self.register(commands)

        self.username_pattern = re.compile(r'^[a-zA-Z0-9_]{4,25}$')

    def register(self, commands):
        commands.register_handler(
            'add alert',
            self.cmd_add_alert,
            user_level=self.user_level,
            description=(
                'Adds streamer alerts to channels\n'
                '\n'
                '`<template>` is optional and allows an alert to have a custom'
                ' message when someone starts streaming. It is a format string'
                ' that stream data is passed through before being sent to the'
                ' channel.\n'
                '\n'
                'The default template is\n'
                '```@here ${channel_name} is now live playing ${game}:\n'
                '${title}\n'
                '${url}```'
                '\n'
                'Possible information you can include in your own templates is:\n'
                '    `${channel_name}`\n'
                '    `${game}`\n'
                '    `${title}`\n'
                '    `${url}`\n'
                '    `${viewers}`\n'
                '    `${followers}`'
            )
        )
        commands.register_handler(
            'remove alert',
            self.cmd_remove_alert,
            user_level=self.user_level,
            description=(
                'Removes streamer alerts from channels'
            )
        )
        commands.register_handler(
            'list alerts',
            self.cmd_list_alerts,
            user_level=self.user_level,
            description=(
                'Lists all streamer alerts currently registered'
            )
        )

    async def cmd_add_alert(self, message, username, channel_name='here', template=''):
        if not self.username_pattern.fullmatch(username):
            raise CommandException(
                'Twitch usernames can only be made from letters, numbers and'
                ' underscores, and must be between 4 and 25 characters long.'
            )

        streamer = self.ensure_streamer(username)

        channel = self.get_channel(channel_name, message)

        if channel.is_private:
            raise CommandException('Alerts in private channels are currently disabled.')

        self.check_permission(message.author, channel)

        streamer_channel = self.build_streamer_channel(
            username,
            streamer,
            channel,
            template
        )

        fmt = 'Alert added for `{0.username}` in `{1}`'

        return await self.bot.send_message(
            message.channel,
            fmt.format(
                streamer,
                self.get_channel_name(channel)
            )
        )

    def ensure_streamer(self, username):
        streamer = database.get_Streamer_by_username(username.lower())

        if not streamer:
            streamer = database.get_Streamer()
            streamer.username = username.lower()
            streamer.save()

        return streamer

    def get_channel(self, name, message):
        if name.lower() == 'here':
            return message.channel

        channel = self.bot.get_channel(name)
        if channel:
            return channel

        # remove hash if user gave one
        if name[0] == '#':
            name = name[1:]

        gen = self.get_channels_with_permission(name, message.author)
        channel = next(gen, None)

        if channel:
            return channel

        raise CommandException('Channel `{}` not found'.format(name))

    def get_channels_with_permission(self, name, member):
        for channel in self.bot.get_all_channels():
            if UserLevel.get(member, channel) < self.user_level:
                continue

            if name in channel.name:
                yield channel

    def check_permission(self, author, channel):
        if UserLevel.get(author, channel) < self.user_level:
            raise CommandException('You do not have access to alerts in that channel')

        if not self.can_send_in(channel):
            raise CommandException(
                'This bot doesn\'t have permission to send and'
                ' read messages in that channel'
            )

    def can_send_in(self, channel):
        if channel.is_private:
            return True

        permissions = channel.permissions_for(channel.server.me)
        return permissions.send_messages

    def build_streamer_channel(self, username, streamer, channel, template):
        if self.streamer_channel_exists(streamer, channel):
            raise CommandException(
                'An alert for `{}` in `{}` already exists'.format(
                    username,
                    self.get_channel_name(channel)
                )
            )

        streamer_channel = database.get_StreamerChannel()
        streamer_channel.streamer_id = streamer.id
        streamer_channel.channel_did = channel.id
        streamer_channel.template = template
        streamer_channel.save()

        return streamer_channel

    def get_channel_name(self, channel):
        if channel.is_private:
            return 'Private ({})'.format(', '.join(r.name for r in (channel.recipients)))

        return '{}#{}'.format(channel.server.name, channel.name)

    def streamer_channel_exists(self, streamer, channel):
        streamer_channels = database.get_StreamerChannel().get_list_by(
            streamer_id=streamer.id,
            channel_did=channel.id
        )

        return bool(streamer_channels)

    async def cmd_remove_alert(self, message, username, channel_name='here'):
        streamer = self.get_streamer(username)

        channel = self.get_channel(channel_name, message)

        self.check_permission(message.author, channel)

        streamer_channel = self.get_streamer_channel(username, streamer, channel)

        streamer_channel.delete()

        await self.bot.send_message(
            message.channel,
            'Alert for `{}` in `{}` deleted'.format(
                streamer.username,
                self.get_channel_name(channel)
            )
        )

        if not streamer.streamer_channels:
            streamer.delete()

    def get_streamer(self, username):
        streamer = database.get_Streamer_by_username(username.lower())
        if not streamer:
            raise CommandException('Streamer `{}` not found'.format(username))

        return streamer

    def get_streamer_channel(self, username, streamer, channel):
        streamer_channel = database.get_StreamerChannel().get_by(
            streamer_id=streamer.id,
            channel_did=channel.id
        )

        if not streamer_channel:
            raise CommandException(
                'Alert for `{}` in `{}` not found'.format(
                    username,
                    self.get_channel_name(channel)
                )
            )

        return streamer_channel

    async def cmd_list_alerts(self, message, username_filter=''):
        alerts = list(self.get_streamer_channels(
            message,
            username_filter.lower(),
            database.get_Streamer_list()
        ))

        await self.bot.send_message(
            message.channel,
            self.get_alerts_text(alerts)
        )

    def get_streamer_channels(self, message, username_filter, streamers):
        for streamer in streamers:
            if username_filter not in streamer.username.lower():
                continue

            yield from self.get_streamer_channels_by_streamer(message, streamer)

    def get_streamer_channels_by_streamer(self, message, streamer):
        for streamer_channel in streamer.streamer_channels:
            channel = streamer_channel.channel

            if UserLevel.get(message.author, channel) >= self.user_level:
                yield streamer_channel

    def get_alerts_text(self, streamer_channels):
        if not streamer_channels:
            return 'No `alerts` found'

        alertfmt = '`{0.streamer.username}` in `{1}`'

        return '\u200C\n{}'.format('\n'.join(
            self.get_alert_channel_text(channel) for channel in streamer_channels
        ))

    def get_alert_channel_text(self, streamer_channel):
        if not streamer_channel.channel:
            streamer_channel.delete()
            return ''

        channel_text = '`{0.streamer.username}` in `{1}`'.format(
            streamer_channel,
            self.get_channel_name(streamer_channel.channel)
        )

        if not self.can_send_in(streamer_channel.channel):
            channel_text += ' (cannot send to channel)'

        return channel_text
