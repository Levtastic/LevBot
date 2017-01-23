import discord
from modules import database
from ..command_handler import CommandException


class AlertCommands:
    def __init__(self, commands):
        self.bot = commands.bot
        self.register(commands)

    def register(self, commands):
        commands.register_handler(self.cmd_add_alert, 'add alert')
        commands.register_handler(self.cmd_edit_alert, 'edit alert')
        commands.register_handler(self.cmd_remove_alert, 'remove alert')
        commands.register_handler(self.cmd_list_alerts, 'list alerts')

    async def cmd_add_alert(self, attributes, message):
        username, channel_name, template = self.get_add_attributes(attributes)

        streamer = self.ensure_streamer(username)

        channel = self.get_channel(channel_name, message)

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
            username, channel_name, template = (attributes.split(' ', 2) + [''])[:3]
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
        if name.lower() == 'here':
            return message.channel

        channel = self.bot.get_channel(name) or discord.utils.get(
            self.bot.get_all_channels(),
            name=name,
            type=discord.ChannelType.text
        )

        if not channel:
            raise CommandException('Channel `{}` not found'.format(name))

        return channel

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
        raise CommandException(
            'Editing alerts is not currently supported.'
            ' Please use `remove alert` and then `add alert` instead'
        )

    async def cmd_remove_alert(self, attributes, message):
        username, channel_name = self.get_remove_attributes(attributes)

        streamer = self.get_streamer(username)

        channel = self.get_channel(channel_name, message)

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
            username, channel_name = attributes.split(' ', 1)
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
        username_filter = attributes.lower()

        streamers = list(filter(
            lambda streamer: username_filter in streamer.username.lower(),
            database.get_Streamer_list()
        ))

        await self.bot.send_message(
            message.channel,
            self.get_alerts_text(streamers)
        )

    def get_alerts_text(self, streamers):
        if not streamers:
            return 'No `alerts` found'

        return '.\n{}'.format('\n'.join(self.get_alerts_text_pieces(streamers)))

    def get_alerts_text_pieces(self, streamers):
        channelfmt = '`{0.server.name}#{0.channel.name}` `({0.id})`'

        for streamer in streamers:
            yield '`{0.username}` `({0.id})`: {1}'.format(
                streamer,
                ', '.join(channelfmt.format(sc) for sc in streamer.streamer_channels)
            )