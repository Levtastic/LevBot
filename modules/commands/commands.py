import sys
import logging
import asyncio
import discord
import settings

from types import MappingProxyType
from collections import defaultdict
from modules import database
from . import model_commands


class Commands:
    def __init__(self):
        self.bot = None
        self.root = CommandHandler('__root__')

        self.register_handler(self.help, 'help')
        
        self.register_handler(self.add, 'add')
        self.register_handler(self._add_alert, 'add alert')
        
        self.register_handler(self.edit, 'edit')
        self.register_handler(self._edit_alert, 'edit alert')
        
        self.register_handler(self.remove, 'remove')
        self.register_handler(self._remove_alert, 'remove alert')
        
        self.register_handler(self.list, 'list')
        self.register_handler(self._list_channels, 'list channels')
        self.register_handler(self._list_users, 'list users')
        self.register_handler(self._list_alerts, 'list alerts')

    def init(self, bot):
        self.bot = bot

    @property
    def register_handler(self):
        return self.root.register_handler

    def handler(self, command):
        def decorator(func):
            self.register_handler(func, command)
            return func

        return decorator

    async def handle_message(self, message):
        command = self._get_command(message)

        if command and self._is_admin(message.author):
            self.root.handle(command, message)

    def _get_command(self, message):
        prefixes = (
            '<@{.id}>'.format(self.bot.user), # standard mention
            '<@!{.id}>'.format(self.bot.user) # nickname mention
        )

        for prefix in prefixes:
            if message.content.startswith(prefix):
                return message.content[len(prefix):].lstrip()

        if message.channel.is_private:
            return message.content

        return ''

    def _is_admin(self, member):
        if str(member) in settings.admin_usernames:
            return True

        return bool(database.get_Admin_by_user_did(member.id))

    async def help(self, attributes, message):
        handler, remainder = self.root.get(attributes)

        if remainder:
            cmd = attributes[:-len(remainder)].strip()
        else:
            cmd = attributes.strip()

        desc = '\n{}\n'.format('-' * 50).join(
            coro.__doc__ for coro in handler.coroutines if coro.__doc__
        )

        cmds = '\n'.join(
            '{} {}'.format(cmd, key) for key in handler.sub_handlers.keys()
        )

        help_text = '.\n'
        help_text += '__{}__:\n\n'.format(cmd) if cmd else ''
        help_text += '**Description:**\n{}\n\n'.format(desc) if desc else ''
        help_text += '**Commands:**\n{}\n\n'.format(cmds) if cmds else ''

        await self.bot.send_message(message.channel, help_text)

    async def add(self, attributes, message):
        add_type, add_attributes = (attributes.split(' ', 1) + [''])[:2]
        return await model_commands.add(self.bot, add_type, add_attributes, message)

    async def edit(self, attributes, message):
        edit_type, edit_attributes = (attributes.split(' ', 1) + [''])[:2]
        return await model_commands.edit(self.bot, edit_type, edit_attributes, message)

    async def remove(self, attributes, message):
        remove_type, remove_attributes = (attributes.split(' ', 1) + [''])[:2]
        return await model_commands.remove(self.bot, remove_type, remove_attributes, message)

    async def list(self, attributes, message):
        list_type, list_filter = (attributes.split(' ', 1) + [''])[:2]
        return await model_commands.list(self.bot, list_type, list_filter, message)

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


class CommandHandler:
    def __init__(self, command):
        self._command = command
        self._sub_handlers = {}
        self._coroutines = []

    @property
    def command(self):
        return self._command

    @property
    def coroutines(self):
        return list(self._coroutines)

    @property
    def sub_handlers(self):
        return MappingProxyType(self._sub_handlers)

    @property
    def is_leaf(self):
        return not self._sub_handlers

    def ensure_sub_handlers(self, commands):
        command, sub_commands = (commands.split(' ', 1) + [''])[:2]
        handler = self._ensure_sub_handler(command)

        if sub_commands:
            return handler.ensure_sub_handlers(sub_commands)

        return handler

    def _ensure_sub_handler(self, command):
        if command not in self._sub_handlers:
            handler = self.__class__(command)
            self._sub_handlers[command] = handler

        return self._sub_handlers[command]

    def register_handler(self, coroutine, command=None):
        if not command:
            self._coroutines.append(coroutine)
            return self

        return self.ensure_sub_handlers(command).register_handler(coroutine)

    def get(self, command_text):
        command, sub_commands = (command_text.split(' ', 1) + [''])[:2]
        command = self._get_command_from_alias(command)

        try:
            return self._sub_handlers[command].get(sub_commands)

        except KeyError:
            return (self, command_text)

    def _get_command_from_alias(self, command):
        alias = database.get_CommandAlias_by_alias(command)
        return alias.command if alias else command

    def handle(self, command, message):
        handler, attributes = self.get(command)
        for coroutine in handler.coroutines:
            asyncio.ensure_future(coroutine(attributes, message))

        return bool(handler.coroutines)


sys.modules[__name__] = Commands()
