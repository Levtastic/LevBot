import logging
import discord

from collections import defaultdict


class Commands:
    def __init__(self, bot):
        self.bot = bot

    async def do_command(self, command, message):
        command_name, command_attributes = (command.split(' ', 1) + [''])[:2]

        aliased_command = self.bot.db.get_command_from_alias(command_name)
        command_name = aliased_command or command_name

        try:
            command_func = getattr(self, command_name.lower())
        except AttributeError:
            return

        await command_func(command_attributes, message)

    async def shutdown(self, attributes, message):
        logging.info('Shutting down')
        await self.bot.send_message(message.channel, 'Shutting down. Goodbye!')
        await self.bot.logout()

    async def list(self, attributes, message):
        list_type, list_filter = (attributes.split(' ', 1) + [''])[:2]

        try:
            command_func = getattr(self, '_list_' + list_type.lower())
        except AttributeError:
            return await self.bot.send_message(message.channel, 'Unknown list type')

        await command_func(list_filter.lower(), message)

    async def add(self, attributes, message):
        add_type, add_attributes = (attributes.split(' ', 1) + [''])[:2]

        try:
            command_func = getattr(self, '_add_' + add_type.lower())
        except AttributeError:
            return await self.bot.send_message(message.channel, 'Unknown add type')

        await command_func(add_attributes, message)

    async def edit(self, attributes, message):
        edit_type, edit_attributes = (attributes.split(' ', 1) + [''])[:2]

        try:
            command_func = getattr(self, '_edit_' + edit_type.lower())
        except AttributeError:
            return await self.bot.send_message(message.channel, 'Unknown edit type')

        await command_func(edit_attributes, message)

    async def remove(self, attributes, message):
        remove_type, remove_attributes = (attributes.split(' ', 1) + [''])[:2]

        try:
            command_func = getattr(self, '_remove_' + remove_type.lower())
        except AttributeError:
            return await self.bot.send_message(message.channel, 'Unknown remove type')

        await command_func(remove_attributes, message)

    async def _list_channels(self, list_filter, message):
        channels = defaultdict(list)
        return_text = '.\n'

        for server in self.bot.servers:
            for channel in server.channels:
                if channel.type == discord.ChannelType.text:
                    if list_filter in channel.name.lower():
                        channels[server].append(channel)

        if not channels:
            return await self.bot.send_message(message.channel, 'No channels found')

        for server in channels.keys():
            return_text += 'Server: {}\n'.format(server)
            for channel in channels[server]:
                return_text += '    {0.id}: {0.name}'.format(channel)

                if not channel.permissions_for(server.me).send_messages:
                    return_text += ' (cannot message)'

                return_text += '\n'

        await self.bot.send_message(message.channel, return_text)

    async def _list_users(self, list_filter, message):
        users = defaultdict(list)
        return_text = '.\n'

        for server in self.bot.servers:
            for member in server.members:
                if list_filter in member.name.lower():
                    users[server].append(member)

        if not users:
            return await self.bot.send_message(message.channel, 'No users found')

        for server in users.keys():
            return_text += 'Server: {}\n'.format(server)
            for member in users[server]:
                return_text += '    {0.id}: {0.name}'.format(member)

                if member.nick:
                    return_text += ' ({0.nick})'.format(member)

                if member.bot:
                    return_text += ' BOT'

                return_text += '\n'

        await self.bot.send_message(message.channel, return_text)

    async def _list_streamers(self, list_filter, message):
        streamers = self.bot.db.get_streamers()
        streamers = [s for s in streamers if list_filter in s[0].lower()]

        if not streamers:
            return await self.bot.send_message(message.channel, 'No streamers found')

        fmt = 'Username: "{0[0]}", Channel: "{0[1]}", Format: "{0[2]}"'
        return_text = '\n'.join(fmt.format(streamer) for streamer in streamers)

        await self.bot.send_message(message.channel, '.\n' + return_text)

    async def _list_streamer_messages(self, list_filter, message):
        streamer_messages = self.bot.db.get_stream_alert_messages()
        streamer_messages = [sm for sm in streamer_messages if list_filter in sm[0].lower()]

        if not streamer_messages:
            return await self.bot.send_message(message.channel, 'No streamer messages found')

        fmt = 'Username: "{0[0]}", Channel: {0[1]}, Message: {0[2]}'
        return_text = '\n'.join(fmt.format(msg) for msg in streamer_messages)

        await self.bot.send_message(message.channel, '.\n' + return_text)

    async def _list_admins(self, list_filter, message):
        admins = self.bot.db.get_admins()
        admins = [a for a in admins if list_filter in a[1].lower()]

        if not admins:
            return await self.bot.send_message(message.channel, 'No admins found')

        return_text = '\n'.join('{0[0]}: {0[1]}'.format(admin) for admin in admins)

        await self.bot.send_message(message.channel, '.\n' + return_text)

    async def _list_aliases(self, list_filter, message):
        aliases = self.bot.db.get_aliases()
        aliases = [a for a in aliases if list_filter in a[1].lower()]

        if not aliases:
            return await self.bot.send_message(message.channel, 'No aliases found')

        return_text = '\n'.join('{0[0]} <- {0[1]}'.format(a) for a in aliases)

        await self.bot.send_message(message.channel, '.\n' + return_text)

    async def _add_streamer(self, attributes, message):
        try:
            username, channel_id, fmt, (attributes.split(' ', 2) + [''])[:3]

            if attr_1.lower() != 'here' and not attr_2:
                raise ValueError('missing attribute')

        except ValueError:
            error = (
                'Correct syntax:\n'
                'add streamer <username> <channel id> <format (optional)>\n'
                'add streamer <username> here <format (optional)>'
            )
            return await self.bot.send_message(message.channel, error)

        if channel_id.lower() == 'here':
            channel_id = message.channel.id

        if self.bot.db.add_streamer(username, channel_id, fmt):
            result = 'Streamer added'
        else:
            result = 'Streamer not added'

        await self.bot.send_message(message.channel, result)

    async def _add_admin(self, attributes, message):
        try:
            user_id, friendly_name = attributes.split(' ', 1)
        except ValueError:
            error = 'Correct syntax: add admin <user_id> <friendly_name>'
            return await self.bot.send_message(message.channel, error)

        if self.bot.db.add_admin(user_id, friendly_name):
            result = 'Admin added'
        else:
            result = 'Admin not added'

        await self.bot.send_message(message.channel, result)

    async def _add_alias(self, attributes, message):
        try:
            command, alias = attributes.split(' ', 1)
        except ValueError:
            error = 'Correct syntax: add alias <command> <alias>'
            return await self.bot.send_message(message.channel, error)

        if self.bot.db.add_alias(command, alias):
            result = 'Alias added'
        else:
            result = 'Alias not added'

        await self.bot.send_message(message.channel, result)

    async def _edit_streamer(self, attributes, message):
        try:
            username, channel_id, fmt = (attributes.split(' ', 2) + [''])[:3]
        except ValueError:
            error = 'Correct syntax: edit streamer <username> <channel id> <format (optional)>'
            return await self.bot.send_message(message.channel, error)

        if self.bot.db.edit_streamer(username, channel_id, fmt):
            result = 'Streamer edited'
        else:
            result = 'Streamer not edited'

        await self.bot.send_message(message.channel, result)

    async def _edit_admin(self, attributes, message):
        try:
            user_id, friendly_name = attributes.split(' ', 1)
        except ValueError:
            error = 'Correct syntax: edit admin <user_id> <friendly_name>'
            return await self.bot.send_message(message.channel, error)

        if self.bot.db.edit_admin(user_id, friendly_name):
            result = 'Admin edited'
        else:
            result = 'Admin not edited'

        await self.bot.send_message(message.channel, result)

    async def _edit_alias(self, attributes, message):
        try:
            command, alias = attributes.split(' ', 1)
        except ValueError:
            error = 'Correct syntax: edit alias <command> <alias>'
            return await self.bot.send_message(message.channel, error)

        if self.bot.db.edit_alias(command, alias):
            result = 'Alias edited'
        else:
            result = 'Alias not edited'

        await self.bot.send_message(message.channel, result)

    async def _remove_streamer(self, attributes, message):
        if not attributes:
            error = 'Correct syntax: remove streamer <username>'
            return await self.bot.send_message(message.channel, error)

        if self.bot.db.remove_streamer(attributes):
            result = 'Streamer removed'
        else:
            result = 'Streamer not removed'

        await self.bot.send_message(message.channel, result)

    async def _remove_streamer_message(self, attributes, message):
        if not attributes:
            error = 'Correct syntax: remove streamer_message <message_id>'
            return await self.bot.send_message(message.channel, error)

        if self.bot.db.remove_stream_alert_message(attributes):
            result = 'Streamer message removed'
        else:
            result = 'Streamer message not removed'

        await self.bot.send_message(message.channel, result)

    async def _remove_admin(self, attributes, message):
        if not attributes:
            error = 'Correct syntax: remove admin <user_id>'
            return await self.bot.send_message(message.channel, error)

        if self.bot.db.remove_admin(attributes):
            result = 'Admin removed'
        else:
            result = 'Admin not removed'

        await self.bot.send_message(message.channel, result)

    async def _remove_alias(self, attributes, message):
        if not attributes:
            error = 'Correct syntax: remove alias <alias>'
            return await self.bot.send_message(message.channel, error)

        if self.bot.db.remove_alias(attributes):
            result = 'Alias removed'
        else:
            result = 'Alias not removed'

        await self.bot.send_message(message.channel, result)
