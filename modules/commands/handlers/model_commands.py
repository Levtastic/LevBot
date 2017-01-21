from functools import partial
from modules import database
from modules.database import models


class ModelCommands:
    def __init__(self, commands):
        self.bot = commands.bot
        self.register(commands)

    def register(self, commands):
        for model in dir(models):
            if not model[0].isupper():
                continue

            commands.register_handler(
                partial(self.add, model),
                'add ' + model
            )
            commands.register_handler(
                partial(self.edit, model),
                'edit ' + model
            )
            commands.register_handler(
                partial(self.remove, model),
                'remove ' + model
            )
            commands.register_handler(
                partial(self.list, model),
                'list ' + model
            )

    async def add(self, model_name, add_attributes, message):
        model = getattr(database, 'get_{}'.format(model_name))()

        if '=' not in add_attributes:
            return await self.bot.send_message(
                message.channel,
                'Syntax: `add {} {}`'.format(
                    model_name,
                    ', '.join('{} = <value>'.format(field) for field in model.fields.keys())
                )
            )

        keyvaluepairs = add_attributes.split(',', len(model.fields) - 1)

        for keyvaluepair in keyvaluepairs:
            field, value = keyvaluepair.split('=', 1)
            field, value = field.strip(), value.strip()

            if field not in model.fields:
                return await self.bot.send_message(
                    message.channel,
                    'Unrecognised field `{}`'.format(field)
                )

            setattr(model, field, value)

        model.save()

        await self.bot.send_message(
            message.channel,
            '`{}` `({})` added'.format(
                model_name,
                model.id
            )
        )

    async def edit(self, model_name, edit_attributes, message):
        model = getattr(database, 'get_{}'.format(model_name))()

        if '=' not in edit_attributes:
            return await self.bot.send_message(
                message.channel,
                'Syntax: `edit {} <search_key> = <search_value>, {}`'.format(
                    model_name,
                    ', '.join('{} = <value>'.format(field) for field in model.fields.keys())
                )
            )

        keyvaluepairs = edit_attributes.split(',', len(model.fields))

        search_field, search_value = keyvaluepairs.pop(0).split('=', 1)
        models = model.get_list_by(**{search_field.strip(): search_value.strip()})

        if len(models) != 1:
            return await self.bot.send_message(
                message.channel,
                'Found {} `{}` models. Unable to remove.'.format(
                    len(models),
                    model_name
                )
            )

        model = models[0]

        for keyvaluepair in keyvaluepairs:
            field, value = keyvaluepair.split('=', 1)
            field, value = field.strip(), value.strip()

            if field not in model.fields:
                return await self.bot.send_message(
                    message.channel,
                    'Unrecognised field `{}`'.format(field)
                )

            setattr(model, field, value)

        model.save()

        await self.bot.send_message(
            message.channel,
            '`{}` `({})` edited'.format(
                model_name,
                model.id
            )
        )

    async def remove(self, model_name, remove_attributes, message):
        model = getattr(database, 'get_{}'.format(model_name))()

        if '=' not in remove_attributes:
            return await self.bot.send_message(
                message.channel,
                'Syntax: `remove {} <key> = <value>`'.format(model_name)
            )

        field, value = remove_attributes.split('=', 1)
        models = model.get_list_by(**{field.strip(): value.strip()})

        if len(models) != 1:
            return await self.bot.send_message(
                message.channel,
                'Found {} `{}` models. Unable to remove.'.format(
                    len(models),
                    model_name
                )
            )

        models[0].delete()

        await self.bot.send_message(
            message.channel,
            '`{}` deleted'.format(model_name)
        )

    async def list(self, model_name, list_filter, message):
        model = getattr(database, 'get_{}'.format(model_name))()

        if '=' in list_filter:
            field, value = list_filter.split('=', 1)
            models = model.get_list_by(**{field.strip(): value.strip()})

        else:
            models = model.get_all()

        if not models:
            return await self.bot.send_message(
                message.channel,
                'No `{}` records found'.format(model_name)
            )

        await self.bot.send_message(
            message.channel,
            '.\n' + '\n'.join(str(model) for model in models)
        )
