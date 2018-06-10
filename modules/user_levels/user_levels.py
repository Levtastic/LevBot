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
    bot_owner          = 8
    global_bot_admin   = 7
    server_owner       = 6
    server_admin       = 5
    server_bot_admin   = 4
    server_user        = 3
    server_blacklisted = 2
    user               = 1
    no_access          = 0
    blacklisted        = -1

    @classmethod
    def get(cls, user, channel_or_server):
        if str(user) in settings.owner_usernames:
            return cls.bot_owner

        db_user = database.get_User_by_user_did(user.id)

        if db_user and db_user.blacklisted:
            return cls.blacklisted

        if db_user and db_user.global_admin:
            return cls.global_bot_admin

        if isinstance(channel_or_server, discord.Server):
            channel = channel_or_server.default_channel
        else:
            channel = channel_or_server

        if channel and channel.is_private:
            return cls._get_private_level(user, channel)

        return cls._get_server_level(user, channel, db_user)

    @classmethod
    def _get_private_level(cls, user, channel):
        if user not in channel.recipients:
            return cls.no_access

        if channel.type == ChannelType.group and user != channel.owner:
            return cls.user

        return cls.server_admin

    @classmethod
    def _get_server_level(cls, user, channel, db_user):
        member = channel.server.get_member(user.id)

        if not member:
            return cls.no_access

        if channel and member == channel.server.owner:
            return cls.server_owner

        if db_user and db_user.is_blacklisted(channel.server):
            return cls.server_blacklisted

        if channel and channel.permissions_for(member).manage_channels:
            return cls.server_admin

        if channel and db_user and db_user.is_admin(channel.server):
            return cls.server_bot_admin

        return cls.server_user
