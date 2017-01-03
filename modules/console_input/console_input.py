import asyncio


class ConsoleInput:
    def __init__(self, bot):
        self.bot = bot

        self.executing = False
        self.latest_code = ''
        self.commands = (
            'exit',
        )

        self.bot.loop.create_task(self.loop())

    async def loop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(0) # let other loops begin before this one

        while not self.bot.is_closed:
            await self.wait_until_not_executing()
            message = await self.get_console_input()

            if message == 'exit':
                print('Shutting down!')
                return await self.bot.logout()

            try:
                self.latest_code = (
                    'async def inner_code(bot):\n' +
                    '    {}\n'.format('\n    '.join(line for line in message.split('\n'))) +
                    'fut = asyncio.ensure_future(inner_code(self.bot))\n' +
                    'fut.add_done_callback(self.on_complete)'
                )
                exec(self.latest_code)

                print('Executing code...')
                self.executing = True

            except BaseException as ex:
                self.print_error(ex)
                self.executing = False

    def print_error(self, ex):
        print('-'*40)
        print(self.latest_code)
        print('-'*40)
        print('{}: {!s}'.format(type(ex).__name__, ex))

    async def wait_until_not_executing(self):
        while self.executing:
            await asyncio.sleep(0)

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

        except BaseException as ex:
            self.print_error(ex)

        self.executing = False
