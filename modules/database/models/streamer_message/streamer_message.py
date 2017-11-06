from discord.utils import cached_slot_property
from discord import NotFound, Forbidden
from ..model import Model
from modules import database


class StreamerMessage(Model):
    @cached_slot_property('_streamer')
    def streamer(self):
        return database.get_Streamer_by_id(self.streamer_id)

    def channel(self):
        return self._streamer_channel.channel

    @cached_slot_property('_streamer_channel')
    def streamer_channel(self):
        sm = database.get_StreamerChannel()
        return sm.get_by(
            streamer_id=self.streamer_id,
            channel_did=self.channel_did
        )

    def define_table(self):
        return 'streamer_messages'

    def define_fields(self):
        return (
            'streamer_id',
            'channel_did',
            'message_did',
        )

    def delete(self, delete_discord_message=True):
        if delete_discord_message:
            self.bot.loop.create_task(self.delete_message())

        super().delete()

    async def delete_message(self):
        message = await self.get_message()
        if message:
            await self.bot.delete_message(message)

    async def get_message(self):
        try:
            return self._message

        except AttributeError:
            if self.channel is None:
                self._message = None

            else:
                try:
                    self._message = await self.bot.get_message(
                        self.channel,
                        self.message_did
                    )

                except (NotFound, Forbidden):
                    self._message = None

            return self._message
