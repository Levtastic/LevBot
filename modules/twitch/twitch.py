import logging
import asyncio
import discord
import aiohttp
import settings


class Twitch:
    message_counter_limit = 20

    def __init__(self, bot):
        self.bot = bot
        self.message_counters = {}

        self.twitch_url_base = 'https://api.twitch.tv/kraken/streams/'
        self.headers = {'Client-ID': settings.twitch_client_id}

        self.bot.loop.create_task(self.loop())

    async def loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed:
            try:
                await self.do_alerts()

            except discord.HTTPException as ex:
                logging.warning('HTTP error {0.status} in Twitch.loop() when fetching {0.url}'.format(ex.response))
                await asyncio.sleep(60)

            except aiohttp.ClientError as ex:
                logging.warning('{} in Twitch.loop(): {!s}'.format(type(ex).__name__, ex))
                await asyncio.sleep(60)

            except (KeyboardInterrupt, SystemExit, GeneratorExit):
                raise

            except:
                if self.bot.is_closed:
                    raise

                logging.exception('Error in Twitch.loop()')
                await asyncio.sleep(300)

    async def do_alerts(self):
        alerts = self.bot.db.get_stream_alerts()

        if not alerts:
            return await asyncio.sleep(10)

        for alert in alerts:
            message = await self.get_message(alert)

            if self.message_missing(alert, message):
                self.bot.db.remove_stream_alert_message(alert['message_did'])
                continue

            message_text = await self.get_twitch_message(
                alert['username'],
                alert['alert_format']
            )

            self.handle_message_counter(message, message_text)

            if self.message_changed(message, message_text):
                await self.edit_message(message, message_text)

            elif self.message_needs_deleting(message, message_text):
                await self.delete_message(message)

            elif self.needs_new_message(message, message_text):
                await self.send_new_message(alert, message_text)

            await asyncio.sleep(1)

    async def get_message(self, alert):
        try:
            message_channel = self.bot.get_channel(alert['message_channel_did'])
            return await self.bot.get_message(message_channel, alert['message_did'])
        except (AttributeError, discord.NotFound):
            return None

    def message_missing(self, alert, message):
        return alert['message_did'] and not message

    async def get_twitch_message(self, username, fmt=''):
        data = await self.get_stream_data(username)
        if not (data and data.get('stream', None)):
            return ''

        fmt = fmt or (
            '@here {0[channel][display_name]} is now live playing {0[channel][game]}:\n'
            '{0[channel][status]}\n'
            '{0[channel][url]}'
        )

        return fmt.format(data['stream'])

    async def get_stream_data(self, username):
        url = self.twitch_url_base + username

        with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as result:
                if not 200 <= result.status < 300:
                    raise discord.HTTPException(result, 'Error fetching twitch api')

                return await result.json()

    def handle_message_counter(self, message, message_text):
        if not message:
            return

        if message_text:
            self.message_counters.pop(message.id, None)

        elif message.id in self.message_counters:
            self.message_counters[message.id] += 1

        else:
            self.message_counters[message.id] = 1

    def message_changed(self,  message, message_text):
        return message and message_text and message.content != message_text

    async def edit_message(self, message, message_text):
        await self.bot.edit_message(message, message_text)

    def message_needs_deleting(self, message, message_text):
        if message and not message_text:
            if self.message_counters[message.id] >= self.message_counter_limit:
                return True

        return False

    async def delete_message(self, message):
        del self.message_counters[message.id]
        await self.bot.delete_message(message)
        self.bot.db.remove_stream_alert_message(message.id)

    def needs_new_message(self, message, message_text):
        return message_text and not message

    async def send_new_message(self, alert, message_text):
        new_channel = self.bot.get_channel(alert['alert_channel_did'])

        new_message = await self.bot.send_message(new_channel, message_text)
        self.bot.db.add_stream_alert_message(
            alert['stream_alert_id'],
            new_channel.id,
            new_message.id
        )
