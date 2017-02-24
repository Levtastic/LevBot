import inspect
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
        handler = self.build_handler(command, coroutine, **kwargs)
        return self.root.register_handler(handler, command)

    def build_handler(self, command, coroutine, **kwargs):
        defaults = {
            'user_level': UserLevel.server_bot_admin,
            'description': '',
            'syntax': self.get_syntax_for(coroutine, command),
        }

        defaults.update(kwargs)

        return Handler(coroutine, **defaults)

    def get_syntax_for(self, coroutine, command):
        parameters = list(inspect.signature(coroutine).parameters.values())

        return '{} {}'.format(
            command,
            ' '.join(self._get_parameter_syntax(p) for p in parameters[1:])
        )

    def _get_parameter_syntax(self, parameter):
        if parameter.default == parameter.empty:
            fmt = '<{0.name}>'
        elif parameter.default is '':
            fmt = '<{0.name} (optional)>'
        else:
            fmt = '<{0.name} (default: "{0.default}")>'

        return fmt.format(parameter)

    def _register_sub_handlers(self):
        for sub_handler in dir(handlers):
            if not sub_handler[0].isupper():
                continue

            getattr(handlers, sub_handler)(self)

    async def cmd_help(self, message, command=''):
        user_level = UserLevel.get(message.author, message.channel)
        dispatcher, remainder = self.root.get(command, user_level)

        if remainder:
            cmd = command[:-len(remainder)].strip()
        else:
            cmd = command.strip()

        level = dispatcher.user_level.name

        desc = self._get_command_description(dispatcher)

        subcmds = self._get_sub_command_names(dispatcher, user_level)
        cmds = '\n'.join('{} {}'.format(cmd, subcmd) for subcmd in subcmds)

        help_text = ''
        if cmd:
            help_text = '`{}`\nMinimum required level: {}\n\n'.format(cmd, level)

        syntax = '\n'.join(
            '`Syntax: {}`'.format(h.syntax) for h in dispatcher.handlers
        )

        help_text += '{}\n\n'.format(syntax) if syntax else ''
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

    def _get_sub_command_names(self, dispatcher, user_level):
        names = []

        for key, value in dispatcher.child_dispatchers.items():
            if value.user_level <= user_level:
                names.append(self._get_full_command_name(key, value))

        return names

    def _get_full_command_name(self, name, dispatcher):
        if len(dispatcher.child_dispatchers) == 1:
            child = list(dispatcher.child_dispatchers.items())[0]
            return '{} {}'.format(name, self._get_full_command_name(*child))

        return name

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
