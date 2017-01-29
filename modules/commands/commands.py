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
            user_level=UserLevel.user
        )

        self._register_sub_handlers()

    def register_handler(self, command, coroutine, **kwargs):
        handler = self.build_handler(coroutine, **kwargs)
        return self.root.register_handler(handler, command)

    def build_handler(self, coroutine, **kwargs):
        defaults = {
            'user_level': UserLevel.server_bot_admin,
        }

        defaults.update(kwargs)

        return Handler(coroutine, **defaults)

    def _register_sub_handlers(self):
        for sub_handler in dir(handlers):
            if not sub_handler[0].isupper():
                continue

            getattr(handlers, sub_handler)(self)

    async def cmd_help(self, attributes, message):
        """Offers help on other commands, and lists sub-commands"""

        dispatcher, remainder = self.root.get(attributes)

        if remainder:
            cmd = attributes[:-len(remainder)].strip()
        else:
            cmd = attributes.strip()

        desc = self._get_command_description(dispatcher)

        cmds = '\n'.join(
            '{} {}'.format(cmd, key) for key in dispatcher.child_dispatchers
        )

        help_text = '.\n'
        help_text += '`{}`\n\n'.format(cmd) if cmd else ''
        help_text += '**Description:**\n{}\n\n'.format(desc) if desc else ''
        help_text += '**Commands:**\n{}\n\n'.format(cmds) if cmds else ''

        await self.bot.send_message(message.channel, help_text)

    def _get_command_description(self, dispatcher):
        pieces = self._get_comment_description_pieces(dispatcher)
        return '\n{}\n'.format('-' * 50).join(pieces)

    def _get_comment_description_pieces(self, dispatcher):
        for handler in dispatcher.handlers:
            description = self._strip_command_description(handler.coroutine.__doc__)
            if description:
                yield description

    def _strip_command_description(self, description):
        if not description:
            return description

        return '\n'.join(line.strip() for line in description.split('\n'))

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
