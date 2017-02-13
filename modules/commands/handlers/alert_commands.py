import discord
from modules import database
from modules import UserLevel
from .. import CommandException


class AlertCommands:
    def __init__(self, commands):
        self.user_level = UserLevel.server_bot_admin

        self.bot = commands.bot
        self.register(commands)

    def register(self, commands):
        commands.register_handler(
            'add alert',
            self.cmd_add_alert,
            user_level=self.user_level
        )
        commands.register_handler(
            'edit alert',
            self.cmd_edit_alert,
            user_level=self.user_level
        )
        commands.register_handler(
            'remove alert',
            self.cmd_remove_alert,
            user_level=self.user_level
        )
        commands.register_handler(
            'list alerts',
            self.cmd_list_alerts,
            user_level=self.user_level
        )

    async def cmd_add_alert(self, attributes, message):
        """Adds streamer alerts to channels

        Syntax: `add alert <username> <channel name/id or "here"> <template>`

        `<template>` is optional and allows an alert to have a custom message when
        someone starts streaming. It is a format string that stream data is passed
        through before being sent to the channel.

        The default template is
        ```@here {0[channel][display_name]} is now live playing {0[channel][game]}:
        {0[channel][status]}
        {0[channel][url]}```

        You can see a list of available information about a stream in the Example Responses here:
        https://github.com/justintv/Twitch-API/blob/master/v3_resources/streams.md#get-streams"""

        username, channel_name, template = self.get_add_attributes(attributes)

        streamer = self.ensure_streamer(username)

        channel = self.get_channel(channel_name, message)

        self.check_permission(message.author, channel)

        streamer_channel = self.build_streamer_channel(
            username,
            streamer,
            channel,
            template
        )

        fmt = ('Alert added for `{0.username}` `({0.id})`'
               ' in `{1.server.name}#{1.channel.name}` `({1.id})`')

        return await self.bot.send_message(
            message.channel,
            fmt.format(streamer, streamer_channel)
        )

    def get_add_attributes(self, attributes):
        try:
            username, channel_name, template = (attributes.split(' ', 2) + ['']*2)[:3]
            return username, channel_name, template

        except ValueError:
            raise CommandException(
                'Syntax: `add alert <username> <channel name/id or "here"> <template>`'
            )

    def ensure_streamer(self, username):
        streamer = database.get_Streamer_by_username(username.lower())

        if not streamer:
            streamer = database.get_Streamer()
            streamer.username = username.lower()
            streamer.save()

        return streamer

    def get_channel(self, name, message):
        if name.lower() in ('', 'here'):
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

    def build_streamer_channel(self, username, streamer, channel, template):
        if self.streamer_channel_exists(streamer, channel):
            raise CommandException(
                'An alert for `{}` in `{}#{}` already exists'.format(
                    username,
                    channel.server.name,
                    channel.name
                )
            )

        streamer_channel = database.get_StreamerChannel()
        streamer_channel.streamer_id = streamer.id
        streamer_channel.channel_did = channel.id
        streamer_channel.template = template
        streamer_channel.save()

        return streamer_channel

    def streamer_channel_exists(self, streamer, channel):
        streamer_channels = database.get_StreamerChannel().get_list_by(
            streamer_id=streamer.id,
            channel_did=channel.id
        )

        return bool(streamer_channels)

    async def cmd_edit_alert(self, attributes, message):
        """Editing alerts is not currently supported.
        Please use `remove alert` and then `add alert` instead"""

        raise CommandException(
            'Editing alerts is not currently supported.'
            ' Please use `remove alert` and then `add alert` instead'
        )

    async def cmd_remove_alert(self, attributes, message):
        """Removes streamer alerts from channels

        Syntax: `remove alert <username> <channel name/id or "here">`"""

        username, channel_name = self.get_remove_attributes(attributes)

        streamer = self.get_streamer(username)

        channel = self.get_channel(channel_name, message)

        self.check_permission(message.author, channel)

        streamer_channel = self.get_streamer_channel(username, streamer, channel)

        streamer_channel.delete()

        await self.bot.send_message(
            message.channel,
            'Alert for `{}` in `#{}` deleted'.format(
                streamer.username,
                channel.name
            )
        )

        if not streamer.streamer_channels:
            streamer.delete()

    def get_remove_attributes(self, attributes):
        try:
            username, channel_name = (attributes.split(' ', 1) + [''])[:2]
            return username, channel_name

        except ValueError:
            raise CommandException(
                'Syntax: `remove alert <username> <channel name/id or "here">`'
            )

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
                'Alert for `{}` in `#{}` not found'.format(
                    username,
                    channel.name
                )
            )

        return streamer_channel

    async def cmd_list_alerts(self, attributes, message):
        """Lists all streamer alerts currently registered

        Syntax: `list alerts`
        or `list alerts <streamer_username>`"""

        alerts = list(self.get_streamer_channels(
            message,
            attributes.lower(),
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

        alertfmt = (
            '`{0.streamer.username}` `({0.streamer.id})`'
            ' `{0.channel.server.name}#{0.channel.name}` `({0.id})`'
        )

        return '.\n{}'.format('\n'.join(
            alertfmt.format(channel) for channel in streamer_channels
        ))
