import settings

from modules import database
from .command_handler import CommandHandler
from . import handlers


class Commands:
    def __init__(self, bot):
        self.bot = bot
        self.root = CommandHandler(bot, '__root__')
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
        """Offers help on other commands, and lists sub-commands"""

        handler, remainder = self.root.get(attributes)

        if remainder:
            cmd = attributes[:-len(remainder)].strip()
        else:
            cmd = attributes.strip()

        desc = self.get_command_description(handler)

        cmds = '\n'.join(
            '{} {}'.format(cmd, key) for key in handler.sub_handlers.keys()
        )

        help_text = '.\n'
        help_text += '__{}__:\n\n'.format(cmd) if cmd else ''
        help_text += '**Description:**\n{}\n\n'.format(desc) if desc else ''
        help_text += '**Commands:**\n{}\n\n'.format(cmds) if cmds else ''

        await self.bot.send_message(message.channel, help_text)

    def get_command_description(self, handler):
        pieces = self.get_comment_description_pieces(handler)
        return '\n{}\n'.format('-' * 50).join(pieces)

    def get_comment_description_pieces(self, handler):
        for coroutine in handler.coroutines:
            description = self.strip_command_description(coroutine.__doc__)
            if description:
                yield description

    def strip_command_description(self, description):
        if not description:
            return description

        return '\n'.join(line.strip() for line in description.split('\n'))

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
