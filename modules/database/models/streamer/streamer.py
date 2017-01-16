from discord.utils import cached_slot_property
from ..model import Model


class Streamer(Model):
    @cached_slot_property('_streamer_channels')
    def streamer_channels(self):
        return self.db.get_StreamerChannel_list_by_streamer_id(self.id)

    @cached_slot_property('_streamer_messages')
    def streamer_messages(self):
        return self.db.get_StreamerMessage_list_by_streamer_id(self.id)

    def define_table(self):
        return 'streamers'

    def define_fields(self):
        return (
            'username',
        )

    def save(self):
        super().save()

        for channel in self.streamer_channels:
            channel.streamer_id = self.id
            channel.save()

        for message in self.streamer_messages:
            message.streamer_id = self.id
            message.save()

    def delete(self):
        for channel in self.streamer_channels:
            channel.delete()

        for message in self.streamer_messages:
            message.delete()

        super().delete()
