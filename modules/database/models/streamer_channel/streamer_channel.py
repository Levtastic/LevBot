from discord.utils import cached_slot_property
from discord import NotFound
from ..model import Model
from modules import database


class StreamerChannel(Model):
    @cached_slot_property('_streamer')
    def streamer(self):
        return database.get_Streamer_by_id(self.streamer_id)

    @cached_slot_property('_channel')
    def channel(self):
        try:
            return self.bot.get_channel(self.channel_did)

        except NotFound:
            return None

    @cached_slot_property('_server')
    def server(self):
        if self.channel:
            return self.channel.server

        return None

    @cached_slot_property('_streamer_messages')
    def streamer_messages(self):
        sm = database.get_StreamerMessage()
        return sm.get_list_by(
            streamer_id=self.streamer_id,
            channel_did=self.channel_did
        )

    def define_table(self):
        return 'streamer_channels'

    def define_fields(self):
        return {
            'streamer_id': None,
            'channel_did': None,
            'template':    '',
        }

    def delete(self):
        for message in self.streamer_messages:
            message.delete()

        super().delete()
