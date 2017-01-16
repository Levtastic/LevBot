async def add(bot, model_name, add_attributes, message):
    model = await _get_model_by_name(bot, model_name, message)
    if not model: return

    if '=' not in add_attributes:
        return await bot.send_message(
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
            return await bot.send_message(
                message.channel,
                'Unrecognised field `{}`'.format(field)
            )

        setattr(model, field, value)

    model.save()

    await bot.send_message(
        message.channel,
        '`{}` `({})` added'.format(
            model_name,
            model.id
        )
    )

async def _get_model_by_name(bot, model_type, message):
    if not model_type:
        await bot.send_message(
            message.channel,
            'Please specify a type from the list in the `help` command'
        )

        return None

    try:
        return getattr(bot.db, 'get_{}'.format(model_type))()

    except (AttributeError, TypeError):
        await bot.send_message(
            message.channel,
            'Unknown type `{}`'.format(model_type)
        )

    return None

async def edit(bot, model_name, edit_attributes, message):
    model = await _get_model_by_name(bot, model_name, message)
    if not model: return

    if '=' not in edit_attributes:
        return await bot.send_message(
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
        return await bot.send_message(
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
            return await bot.send_message(
                message.channel,
                'Unrecognised field `{}`'.format(field)
            )

        setattr(model, field, value)

    model.save()

    await bot.send_message(
        message.channel,
        '`{}` `({})` edited'.format(
            model_name,
            model.id
        )
    )

async def remove(bot, model_name, remove_attributes, message):
    model = await _get_model_by_name(bot, model_name, message)
    if not model: return

    if '=' not in remove_attributes:
        return await bot.send_message(
            message.channel,
            'Syntax: `remove {} <key> = <value>`'.format(model_name)
        )

    field, value = remove_attributes.split('=', 1)
    models = model.get_list_by(**{field.strip(): value.strip()})

    if len(models) != 1:
        return await bot.send_message(
            message.channel,
            'Found {} `{}` models. Unable to remove.'.format(
                len(models),
                model_name
            )
        )

    models[0].delete()

    await bot.send_message(
        message.channel,
        '`{}` deleted'.format(model_name)
    )

async def list(bot, model_name, list_filter, message):
    model = await _get_model_by_name(bot, model_name, message)
    if not model: return

    if '=' in list_filter:
        field, value = list_filter.split('=', 1)
        models = model.get_list_by(**{field.strip(): value.strip()})

    else:
        models = model.get_all()

    if not models:
        return await bot.send_message(
            message.channel,
            'No `{}` records found'.format(model_name)
        )

    await bot.send_message(
        message.channel,
        '.\n' + '\n'.join(str(model) for model in models)
    )
