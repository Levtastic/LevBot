from ..model import Model


class User(Model):
    def _build_from_fields(self, fields):
        model = super()._build_from_fields(fields)
        model.global_admin = bool(model.global_admin)
        model.blacklisted = bool(model.blacklisted)
        return model

    async def get_user(self):
        try:
            return self._user

        except AttributeError:
            self._user = await self.bot.get_user_info(self.user_did)
            return self._user

    def define_table(self):
        return 'users'

    def define_fields(self):
        return {
            'user_did': None,
            'global_admin': False,
            'blacklisted': False,
        }
