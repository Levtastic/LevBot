from functools import partial
from sqlite3 import IntegrityError
from modules import database
from modules.database import models
from ..command_handler import CommandException


class ModelCommands:
    def __init__(self, commands):
        self.bot = commands.bot
        self.register(commands)

    def register(self, commands):
        for model in dir(models):
            if not model[0].isupper():
                continue

            self.register_model(commands, model)

    def register_model(self, commands, model):
        for command in ('add', 'edit', 'remove', 'list'):
            commands.register_handler(
                self.get_partial(command, model),
                '{} {}'.format(command, model)
            )

    def get_partial(self, command, model):
        func_name = 'cmd_{}'.format(command)
        native_func = getattr(self, func_name)
        partial_func = partial(native_func, model)
        partial_func.__doc__ = native_func.__doc__
        return partial_func

    async def cmd_add(self, model_name, attributes, message):
        """Adds a model to the database manually

        The syntax of this command is determined at runtime
        To see it, run the command without any parameters"""

        model = self.get_model(model_name)

        syntax_message = 'Syntax: `add {} {}`'.format(
            model_name,
            ', '.join('{} = <value>'.format(field) for field in model.fields)
        )

        try:
            pairs = list(self.get_attribute_pairs(attributes, model))

        except ValueError:
            raise CommandException(syntax_message)

        if not pairs:
            raise CommandException(syntax_message)

        self.set_model_attributes(model, pairs)

        try:
            model.save()

        except IntegrityError:
            raise CommandException(
                'One or more required fields were left out of the command'
            )

        await self.bot.send_message(
            message.channel,
            '`{}` `({})` added'.format(
                model_name,
                model.id
            )
        )

    def get_model(self, model_name):
        factory_name = 'get_{}'.format(model_name)
        factory = getattr(database, factory_name)
        return factory()

    def get_attribute_pairs(self, attributes, model, count_override=None):
        count = (count_override or len(model.fields)) - 1

        for pair in attributes.split(',', count):
            field, value = pair.split('=', 1)
            field, value = field.strip(), value.strip()

            if not field in model.fields:
                raise CommandException('Unrecognised field `{}`'.format(field))

            yield field, value

    def set_model_attributes(self, model, pairs):
        for field, value in pairs:
            setattr(model, field, value)

    async def cmd_edit(self, model_name, attributes, message):
        """Edits a model in the database manually

        The syntax of this command is determined at runtime
        To see it, run the command without any parameters"""

        model = self.get_model(model_name)

        syntax_message = 'Syntax: `edit {} <search_key> = <search_value>, {}`'.format(
            model_name,
            ', '.join('{} = <value>'.format(field) for field in model.fields.keys())
        )

        try:
            print(repr(attributes))
            pairs = list(self.get_attribute_pairs(
                attributes,
                model
            ))

        except ValueError:
            raise CommandException(syntax_message)

        if len(pairs) < 2:
            raise CommandException(syntax_message)

        model = self.search_for_model(model, *pairs.pop(0))

        self.set_model_attributes(model, pairs)

        model.save()

        await self.bot.send_message(
            message.channel,
            '`{}` `({})` edited'.format(
                model_name,
                model.id
            )
        )

    def search_for_model(self, model, field, value):
        models = model.get_list_by(**{field: value})

        if not models:
            raise CommandException(
                'No {} models found with these parameters'.format(
                    type(model).__name__
                )
            )

        if len(models) != 1:
            raise CommandException(
                'This operation only works on one {} at a time, but we found {}'.format(
                    type(model).__name__,
                    len(models)
                )
            )

        return models[0]

    async def cmd_remove(self, model_name, attributes, message):
        """Removes a model from the database manually

        The syntax of this command is determined at runtime
        To see it, run the command without any parameters"""

        model = self.get_model(model_name)

        syntax_message = 'Syntax: `remove {} <key> = <value>`'.format(model_name)

        try:
            pairs = list(self.get_attribute_pairs(attributes, model))

        except ValueError:
            raise CommandException(syntax_message)

        if len(pairs) != 1:
            raise CommandException(syntax_message)

        model = self.search_for_model(model, *pairs[0])

        model.delete()

        await self.bot.send_message(
            message.channel,
            '`{}` deleted'.format(model_name)
        )

    async def cmd_list(self, model_name, attributes, message):
        """Lists models in the database

        The syntax of this command is determined at runtime
        To see it, run the command without any parameters"""

        model = self.get_model(model_name)

        if attributes:
            try:
                pairs = list(self.get_attribute_pairs(attributes, model))

            except ValueError:
                raise CommandException(
                    'Syntax: `list {} <key> = <value>`'.format(model_name)
                )

        else:
            pairs = []

        models = self.filter_model(model, pairs)

        if not models:
            return await self.bot.send_message(
                message.channel,
                'No `{}` records found'.format(model_name)
            )

        await self.bot.send_message(
            message.channel,
            '.\n' + '\n'.join(str(model) for model in models)
        )

    def filter_model(self, model, pairs):
        if pairs:
            list_filter = {field: value for field, value in pairs}
            return model.get_list_by(**list_filter)

        return model.get_all()
