from ..model import Model


class Admin(Model):
    async def get_user(self):
        try:
            return self._user

        except AttributeError:
            self._user = await self.bot.get_user_info(self.user_did)
            return self._user

    def define_table(self):
        return 'admins'

    def define_fields(self):
        return (
            'user_did',
        )
