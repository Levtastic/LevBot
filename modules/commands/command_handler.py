import asyncio

from types import MappingProxyType
from modules import database


class CommandHandler:
    def __init__(self, bot, command):
        self._bot = bot
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
            handler = self.__class__(self._bot, command)
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
            asyncio.ensure_future(self._wrapper(coroutine, attributes, message))

        return bool(handler.coroutines)

    async def _wrapper(self, coroutine, attributes, message):
        try:
            await coroutine(attributes, message)

        except CommandException as ex:
            await self._bot.send_message(message.channel, str(ex))


class CommandException(Exception):
    pass
