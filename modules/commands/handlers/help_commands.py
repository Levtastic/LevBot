import discord
from modules import database
from modules import UserLevel
from .. import CommandException


class HelpCommands:
    def __init__(self, commands):
        self.commands = commands
        self.bot = commands.bot

        self.register()

    def register(self):
        self.commands.register_handler(
            'help',
            self.cmd_help,
            user_level=UserLevel.user,
            description=(
                'Offers help on other commands, and lists sub-commands'
            )
        )

    async def cmd_help(self, message, command=''):
        user_level = UserLevel.get(message.author, message.channel)
        dispatcher, remainder = self.commands.root.get(command, user_level)

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
