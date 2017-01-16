import logging
import asyncio
import discord
import aiohttp
import settings

from collections import defaultdict
from concurrent.futures import CancelledError


class Twitch:
    def __init__(self, bot):
        self.bot = bot
        self.offline_counters = defaultdict(int)

        self.twitch_url_base = 'https://api.twitch.tv/kraken/streams/'
        self.headers = {'Client-ID': settings.twitch_client_id}

        self.counter = Counter(maximum=20)

        bot.loop.create_task(self.loop())

    async def loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed:
            streamers = self.bot.db.get_Streamer_list()

            for streamer in streamers:
                await self.insulate(self.do_streamer_alerts, streamer)
                await asyncio.sleep(1)

            if not streamers:
                await asyncio.sleep(10)

    async def insulate(self, func, *args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except discord.HTTPException as ex:
            logging.warning((
                'Error in Twitch.loop() when fetching {0.response.url}:  {0!s}'
            ).format(ex))
            await asyncio.sleep(60)

        except aiohttp.ClientError as ex:
            logging.warning('{} in Twitch.loop(): {!s}'.format(type(ex).__name__, ex))
            await asyncio.sleep(60)

        except (KeyboardInterrupt, SystemExit, GeneratorExit, CancelledError):
            raise

        except:
            logging.exception('Error in Twitch.loop()')
            await asyncio.sleep(300)

    async def do_streamer_alerts(self, streamer):
        data = await self.get_stream_data(streamer.username)
        data = data and data.get('stream', None)

        if data:
            return await self.handle_streaming(streamer, data)

        else:
            return await self.handle_not_streaming(streamer)

    async def get_stream_data(self, username):
        url = self.twitch_url_base + username

        with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as result:
                if not 200 <= result.status < 300:
                    raise discord.HTTPException(result, 'Error fetching twitch api')

                return await result.json()

    async def handle_streaming(self, streamer, twitch_data):
        self.offline_counters.pop(streamer.username, None)

        for streamer_channel in streamer.streamer_channels:
            fmt = streamer_channel.template or (
                '@here {0[channel][display_name]} is now live playing {0[channel][game]}:\n'
                '{0[channel][status]}\n'
                '{0[channel][url]}'
            )

            text = fmt.format(twitch_data)
            await self.send_or_update_message(streamer_channel, text)

    async def send_or_update_message(self, streamer_channel, text):
        if not streamer_channel.streamer_messages:
            return await self.send_message(streamer_channel, text)

        for streamer_message in streamer_channel.streamer_messages:
            await self.update_message(streamer_message, text)

    async def send_message(self, streamer_channel, text):
        message = await self.bot.send_message(streamer_channel.channel, text)

        streamer_message = self.bot.db.get_StreamerMessage()
        streamer_message.channel_did = streamer_channel.channel.id
        streamer_message.message_did = message.id

        streamer = streamer_channel.streamer
        streamer.streamer_messages.append(streamer_message)
        streamer.save()

    async def update_message(self, streamer_message, text):
        message = await streamer_message.get_message()
        if not message:
            return await self.replace_message(streamer_message, text)

        if message.content != text:
            return await self.bot.edit_message(message, text)

    async def replace_message(self, streamer_message, text):
        streamer_message.delete()
        return await self.send_message(
            streamer_message.streamer_channel,
            text
        )

    async def handle_not_streaming(self, streamer):
        if streamer.streamer_messages and self.counter.click(streamer.username):
            for streamer_message in streamer.streamer_messages:
                streamer_message.delete()


class Counter:
    def __init__(self, maximum):
        self.maximum = maximum
        self.values = defaultdict(int)

    def click(self, key='__default__'):
        self.values[key] += 1

        if self.values[key] > self.maximum:
            del self.values[key]
            return True

        return False
