import sys
import asyncio
import settings

from types import MappingProxyType
from modules import database
from . import handlers


class Commands:
    def __init__(self, bot):
        self.bot = bot
        self.root = CommandHandler('__root__')
        self.register_handler(self.cmd_help, 'help')

        self.register_sub_handlers()

    @property
    def register_handler(self):
        return self.root.register_handler

    def register_sub_handlers(self):
        for sub_handler in dir(handlers):
            if not sub_handler[0].isupper():
                continue

            getattr(handlers, sub_handler)(self)

    async def cmd_help(self, attributes, message):
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

    def handle_message(self, message):
        command = self._get_command(message)

        if command and self._is_admin(message.author):
            return self.root.handle(command, message)

        return False

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
