import discord
import settings

from enum import Enum
from discord import ChannelType
from modules import database


class OrderedEnum(Enum):
    """lifted from https://docs.python.org/3/library/enum.html#orderedenum"""

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value

        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value

        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value

        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value

        return NotImplemented


class UserLevel(OrderedEnum):
    bot_owner        = 7
    global_bot_admin = 6
    server_owner     = 5
    server_admin     = 4
    server_bot_admin = 3
    server_user      = 2
    user             = 1
    no_access        = 0
    blacklisted      = -1

    @classmethod
    def get(cls, member, channel=None):
        if str(member) in settings.owner_usernames:
            return cls.bot_owner

        db_user = database.get_User_by_user_did(member.id)

        if db_user and db_user.blacklisted:
            return cls.blacklisted

        if db_user and db_user.global_admin:
            return cls.global_bot_admin

        if channel and channel.is_private:
            return cls._get_private_level(member, channel)

        if channel and isinstance(member, discord.Member):
            return cls._get_server_level(member, channel, db_user)

        return cls.user

    @classmethod
    def _get_private_level(cls, member, channel):
        if member not in channel.recipients:
            return cls.no_access

        if channel.type == ChannelType.group and member != channel.owner:
            return cls.user

        return cls.server_admin

    @classmethod
    def _get_server_level(cls, member, channel, db_user):
        if member == channel.server.owner:
            return cls.server_owner

        if channel.permissions_for(member).manage_channels:
            return cls.server_admin

        if db_user and db_user.is_admin(channel.server):
            return cls.server_bot_admin

        if member in channel.server.members:
            return cls.server_user

        return cls.user
