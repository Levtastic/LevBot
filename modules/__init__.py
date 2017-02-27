from .database import database
from .user_levels.user_levels import UserLevel
from .commands.commands import Commands
from .twitch.twitch import Twitch
from .console_input.console_input import ConsoleInput

to_init = [
	database,
	Commands,
	Twitch,
	ConsoleInput,
]
