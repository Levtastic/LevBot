import time
import logging
import asyncio
import discord
import aiohttp
import settings

from string import Template
from collections import defaultdict
from concurrent.futures import CancelledError, TimeoutError
from discord import NotFound, Forbidden
from modules import database
from utils import escape


class Twitch:
    def __init__(self, bot):
        self.bot = bot

        self.api = Api(settings.twitch_client_id)
        self.counter = Counter(maximum=20)

        bot.loop.create_task(self.loop())

    async def loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed:
            streamers = database.get_Streamer_list()

            if streamers:
                await self.insulate(self.do_streamer_alerts, streamers)

            else:
                await asyncio.sleep(10)

    async def insulate(self, func, *args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except discord.HTTPException as ex:
            logging.warning((
                'Error in Twitch.loop() when fetching {0.response.url}: {0!s}'
            ).format(ex))
            await asyncio.sleep(60)

        except (aiohttp.ClientError, ConnectionResetError, TimeoutError) as ex:
            logging.warning('{} in Twitch.loop(): {!s}'.format(
                type(ex).__name__,
                ex
            ))
            await asyncio.sleep(60)

        except (KeyboardInterrupt, SystemExit, GeneratorExit, CancelledError):
            raise

        except:
            logging.exception('Error in Twitch.loop()')
            await asyncio.sleep(300)

    async def do_streamer_alerts(self, streamers):
        await self.update_ids(streamers)

        ids = [streamer.twitch_id for streamer in streamers]
        streamer_data = await self.api.get_streams(ids)

        for streamer in streamers:
            if not streamer.streamer_channels:
                streamer.delete()
                continue

            data = streamer_data[streamer.twitch_id]

            if data:
                await self.handle_streaming(streamer, data)

            else:
                await self.handle_not_streaming(streamer)

    async def update_ids(self, streamers):
        streamers = [s for s in streamers if not s.twitch_id]
        usernames = [s.username for s in streamers]

        user_data = await self.api.get_users(usernames)

        for streamer in streamers:
            if user_data[streamer.username] is None:
                streamer.delete()
                continue

            streamer.twitch_id = str(user_data[streamer.username]['_id'])
            streamer.save()

    async def handle_streaming(self, streamer, twitch_data):
        self.counter.reset(streamer.username)

        for streamer_channel in streamer.streamer_channels:
            template = streamer_channel.template or (
                '@here ${channel_name} is now live playing ${game}:\n'
                '${title}\n'
                '${url}'
            )

            text = self.apply_template(template, twitch_data)
            await self.send_or_update_message(streamer_channel, text)

    def apply_template(self, template, twitch_data):
        return Template(template).safe_substitute(
            channel_name=escape(twitch_data['channel']['display_name']),
            game=escape(twitch_data['channel']['game']) or 'nothing',
            title=escape(twitch_data['channel']['status']),
            url=twitch_data['channel']['url'],
            viewers=twitch_data['viewers'],
            followers=twitch_data['channel']['followers']
        )

    async def send_or_update_message(self, streamer_channel, text):
        try:
            if not streamer_channel.streamer_messages:
                return await self.send_message(streamer_channel, text)

            for streamer_message in streamer_channel.streamer_messages:
                await self.update_message(streamer_message, text)

        except (NotFound, Forbidden):
            pass

    async def send_message(self, streamer_channel, text):
        # don't send anything long enough to clip into multiple messages
        text = text[:self.bot.max_message_len]

        channel = streamer_channel.channel
        if channel is None:
            return

        message = await self.bot.send_message(channel, text)

        streamer_message = database.get_StreamerMessage()
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
        if (streamer.streamer_messages and
                self.counter.click(streamer.username)):
            for streamer_message in streamer.streamer_messages:
                streamer_message.delete()


class Api:
    def __init__(self, client_id, batch_size=100, timeout_delay=1):
        self.url_root = 'https://api.twitch.tv/kraken/'
        self.headers = {
            'Accept': 'application/vnd.twitchtv.v5+json',
            'Client-ID': client_id,
        }
        self.timeout_delay = timeout_delay
        self.batch_size = batch_size

        self.url_users = self.url_root + (
            'users'
            '?login={}'
        )

        self.url_streams = self.url_root + (
            'streams'
            '?limit=100'
            '&stream_type=live'
            '&channel={}'
        )

        self.last_timeout = time.perf_counter() - timeout_delay

    async def get_users(self, usernames):
        responses = await self.get_responses(self.url_users, usernames)

        data = {username: None for username in usernames}
        for response in responses:
            for user in response.get('users', []):
                data[user['name']] = user

        return data

    async def get_streams(self, uids):
        responses = await self.get_responses(self.url_streams, uids)

        data = {uid: None for uid in uids}
        for response in responses:
            for stream in response.get('streams', []):
                data[str(stream['channel']['_id'])] = stream

        return data

    async def get_responses(self, url, pieces):
        responses = []
        for i in range(0, len(pieces), self.batch_size):
            pieces_batch = pieces[i:i + self.batch_size]
            responses.append(await self.get_responses_batch(url, pieces_batch))

        return responses

    async def get_responses_batch(self, url, pieces):
        if not pieces:
            return {}

        url = url.format(','.join(pieces))
        response = await self.do_query(url)

        return response

    async def do_query(self, url):
        await self.timeout()

        with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as result:
                if not 200 <= result.status < 300:
                    raise discord.HTTPException(
                        result,
                        'Error fetching twitch api'
                    )

                return await result.json(encoding='utf-8')

    async def timeout(self):
        time_since = time.perf_counter() - self.last_timeout
        time_until = self.timeout_delay - time_since
        wait_time = max(0, time_until)

        await asyncio.sleep(wait_time)

        self.last_timeout = time.perf_counter()


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

    def reset(self, key='__default__'):
        self.values.pop(key, None)
