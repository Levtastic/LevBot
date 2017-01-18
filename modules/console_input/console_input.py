import traceback
import asyncio

from concurrent.futures import CancelledError


class ConsoleInput:
    def __init__(self, bot):
        self.bot = bot

        self.is_ready = asyncio.Event()
        self.commands = (
            'exit',
        )

        self.bot.loop.create_task(self.loop())

    async def loop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(0) # let other loops begin before this one

        self.is_ready.set()

        while not self.bot.is_closed:
            await self.is_ready.wait()
            message = await self.get_console_input()

            if message == 'exit':
                print('Shutting down!')
                await self.bot.logout()
                raise KeyboardInterrupt()

            try:
                exec(
                    'async def console(bot):\n' +
                    ' {}\n'.format('\n '.join(line for line in message.split('\n'))) +
                    'fut = asyncio.ensure_future(console(self.bot))\n' +
                    'fut.add_done_callback(self.on_complete)'
                )

                print('Executing code...')
                self.is_ready.clear()

            except (KeyboardInterrupt, SystemExit, GeneratorExit, CancelledError):
                raise

            except:
                traceback.print_exc()

    async def get_console_input(self):
        lines = []

        while not self.bot.is_closed:
            line = await self.bot.loop.run_in_executor(None, input, '> ')

            command = line.lower()

            if not lines and command in self.commands:
                return command

            if line:
                lines.append(line)

            elif lines:
                return '\n'.join(lines)

    def on_complete(self, fut):
        try:
            print('Code completed - result: ' + repr(fut.result()))

        except (KeyboardInterrupt, SystemExit, GeneratorExit, CancelledError):
            raise

        except:
            traceback.print_exc()

        self.is_ready.set()
