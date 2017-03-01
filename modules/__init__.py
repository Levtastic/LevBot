from .database import database
from .user_levels.user_levels import UserLevel
from .commands.commands import Commands
from .twitch.twitch import Twitch
from .console_input.console_input import ConsoleInput


def init(bot):
	modules = (
		database,
		Commands,
		Twitch,
		ConsoleInput,
	)

	for module in modules:
		module(bot)
