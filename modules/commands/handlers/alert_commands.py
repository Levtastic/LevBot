from modules import commands
from modules import database


class AlertCommands:
    def __init__(self, commands):
        self.bot = commands.bot
        self.register(commands)

    def register(self, commands):
        commands.register_handler(self._add_alert, 'add alert')
        commands.register_handler(self._edit_alert, 'edit alert')
        commands.register_handler(self._remove_alert, 'remove alert')
        commands.register_handler(self._list_alerts, 'list alerts')

    async def _add_alert(self, attributes, message):
        try:
            username, channel_name, template = (attributes.split(' ', 2) + [''])[:3]

        except ValueError:
            return await self.bot.send_message(
                message.channel,
                'Syntax: `add alert <username> <channel name/id or "here"> <template>`'
            )

        streamer = database.get_Streamer_by_username(username.lower())
        if not streamer:
            streamer = database.get_Streamer()
            streamer.username = username.lower()
            streamer.save()

        channel = self._get_channel_by_name(channel_name, message)
        if not channel:
            return await self.bot.send_message(
                message.channel,
                'Channel `{}` not found'.format(
                    channel_name
                )
            )

        streamer_channel = database.get_StreamerChannel()
        if streamer_channel.get_list_by(streamer_id=streamer.id,
                                    channel_did=channel.id):
            return await self.bot.send_message(
                message.channel,
                'An alert for `{}` in `{}#{}` already exists'.format(
                    username,
                    channel.server.name,
                    channel.name
                )
            )

        streamer_channel.streamer_id = streamer.id
        streamer_channel.channel_did = channel.id
        streamer_channel.template = template
        streamer_channel.save()

        fmt = ('Alert added for `{0.username}` `({0.id})`'
               ' in `{1.server.name}#{1.channel.name}` `({1.id})`')

        return await self.bot.send_message(
            message.channel,
            fmt.format(streamer, streamer_channel)
        )

    def _get_channel_by_name(self, name, message):
        if name.lower() == 'here':
            return message.channel

        return self.bot.get_channel(name) or discord.utils.get(
            self.bot.get_all_channels(),
            name=name,
            type=discord.ChannelType.text
        )

    async def _edit_alert(self, attributes, message):
        await self.bot.send_message(
            message.channel,
            'Editing alerts is not currently supported. '
            'Please use `remove alert` and then `add alert` instead'
        )

    async def _remove_alert(self, attributes, message):
        try:
            username, channel_name = attributes.split(' ', 2)

        except ValueError:
            return await self.bot.send_message(
                message.channel,
                'Syntax: `remove alert <username> <channel name/id or "here">`'
            )

        streamer = database.get_Streamer_by_username(username.lower())
        if not streamer:
            return await self.bot.send_message(
                message.channel,
                'Streamer `{}` not found'.format(username)
            )

        channel = self._get_channel_by_name(channel_name, message)
        if not channel:
            return await self.bot.send_message(
                message.channel,
                'Channel `#{}` not found'.format(
                    channel_name
                )
            )

        streamer_channel = database.get_StreamerChannel().get_by(
            streamer_id=streamer.id,
            channel_did=channel.id
        )

        if not streamer_channel:
            return await self.bot.send_message(
                message.channel,
                'Alert for `{}` in `#{}` not found'.format(
                    username,
                    channel_name
                )
            )

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

    async def _list_alerts(self, username_filter, message):
        username_filter = username_filter.lower()
        return_text = ''

        streamers = database.get_Streamer_list()

        for streamer in streamers:
            if username_filter not in streamer.username.lower():
                continue

            fmt = '`{0.server.name}#{0.channel.name}` `({0.id})`'

            return_text += '`{0.username}` `({0.id})`: {1}\n'.format(
                streamer,
                ', '.join(fmt.format(sc) for sc in streamer.streamer_channels)
            )

        if not return_text:
            return await self.bot.send_message(
                message.channel,
                'No `alerts` found'
            )

        await self.bot.send_message(message.channel, '.\n' + return_text)
