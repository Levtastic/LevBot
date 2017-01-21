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
