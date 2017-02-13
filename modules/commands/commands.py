import settings

from modules import database
from modules import UserLevel
from . import CommandDispatcher, Handler
from . import handlers


class Commands:
    def __init__(self, bot):
        self.bot = bot
        self.root = CommandDispatcher(bot, '__root__')

        self.register_handler(
            'help',
            self.cmd_help,
            user_level=UserLevel.user,
            description='Offers help on other commands, and lists sub-commands'
        )

        self._register_sub_handlers()

    def register_handler(self, command, coroutine, **kwargs):
        handler = self.build_handler(coroutine, **kwargs)
        return self.root.register_handler(handler, command)

    def build_handler(self, coroutine, **kwargs):
        defaults = {
            'user_level': UserLevel.server_bot_admin,
            'description': '',
        }

        defaults.update(kwargs)

        return Handler(coroutine, **defaults)

    def _register_sub_handlers(self):
        for sub_handler in dir(handlers):
            if not sub_handler[0].isupper():
                continue

            getattr(handlers, sub_handler)(self)

    async def cmd_help(self, attributes, message):
        user_level = UserLevel.get(message.author, message.channel)
        dispatcher, remainder = self.root.get(attributes, user_level)

        if remainder:
            cmd = attributes[:-len(remainder)].strip()
        else:
            cmd = attributes.strip()

        desc = self._get_command_description(dispatcher)

        cmds = ''
        for key, value in dispatcher.child_dispatchers.items():
            if value.user_level <= user_level:
                cmds += '{} {}\n'.format(cmd, key)

        help_text = '`{0}`\n\n'.format(cmd) if cmd else ''
        help_text += '**Description:**\n{}\n\n'.format(desc) if desc else ''
        help_text += '**Commands:**\n{}\n\n'.format(cmds) if cmds else ''

        await self.bot.send_message(message.author, help_text)

    def _get_command_description(self, dispatcher):
        pieces = self._get_comment_description_pieces(dispatcher)
        return '\n{}\n'.format('-' * 50).join(pieces)

    def _get_comment_description_pieces(self, dispatcher):
        for handler in dispatcher.handlers:
            if handler.description:
                yield handler.description

    def handle_message(self, message):
        command = self._get_command(message)

        if command:
            return self.root.dispatch(command, message)

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
