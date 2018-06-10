import sys
import sqlite3
import settings

from contextlib import closing


class Database:
    def __init__(self):
        self.bot = None

        self.database = sqlite3.connect(settings.db_name)
        self.database.row_factory = sqlite3.Row

    def __call__(self, bot):
        self.bot = bot

    def __getattr__(self, name):
        if name.startswith('get_'):
            return self.get_model_factory(name[4:].split('_'))

        raise AttributeError("'{}' object has no attribute '{}'".format(
            type(self).__name__,
            name
        ))

    def get_model_factory(self, attrs):
        # db.get_Model()                    # empty
        # db.get_Model_by_field(field)      # one
        # db.get_Model_list()               # all
        # db.get_Model_list_by_field(field) # list

        model_name = attrs.pop(0)

        if not attrs:
            return lambda: self.get_initialised_model(model_name)

        model = self.get_initialised_model(model_name)

        if attrs.pop(0) == 'by':  # or 'list'
            func_name = 'get_by_{}'.format('_'.join(attrs))
            return getattr(model, func_name)

        if not attrs:
            return model.get_all

        attrs.pop(0)  # 'by'

        func_name = 'get_list_by_{}'.format('_'.join(attrs))

        return getattr(model, func_name)

    def get_initialised_model(self, name):
        # imported here so database will be initialised when models import it
        from . import models
        model = getattr(models, name)
        return model(self.bot)

    def execute(self, query, parameters=(), script=False, commit=True):
        parameters = self._convert_parameters(parameters)

        with closing(self.database.cursor()) as cursor:
            if script: cursor.executescript(query)
            else: cursor.execute(query, parameters)

            if commit:
                self.database.commit()

            return cursor.lastrowid

    def _convert_parameters(self, parameters):
        if isinstance(parameters, (tuple, list, dict)):
            return parameters

        return (parameters, )

    def fetch_all(self, query, parameters=()):
        parameters = self._convert_parameters(parameters)

        with closing(self.database.cursor()) as cursor:
            cursor.execute(query, parameters)

            return cursor.fetchall()

    def fetch_row(self, query, parameters=()):
        parameters = self._convert_parameters(parameters)

        with closing(self.database.cursor()) as cursor:
            cursor.execute(query, parameters)

            return cursor.fetchone()

    def fetch_value(self, query, parameters=(), *args, **kwargs):
        parameters = self._convert_parameters(parameters)

        try:
            return self.fetch_row(query, parameters)[0]

        except IndexError:
            if args: return args[0]
            return kwargs.pop('default')

    def insert(self, table, fields):
        query = 'INSERT INTO {} ({}) VALUES ({})'

        fieldnames = fields.keys()

        query = query.format(
            table,
            ','.join(fieldnames),
            ','.join(':{}'.format(name) for name in fieldnames)
        )

        return self.execute(query, fields)

    def update(self, table, fields, where_query='', where_args={}, **kwargs):
        query = 'UPDATE {} SET {} WHERE {}'

        fieldnames = tuple(fields.keys())

        if where_query:
            fields.update(where_args)

        else:
            fields.update({
                'where_' + key: value for key, value in kwargs.items()
            })
            where_query = ' AND '.join(
                '{0} = :where_{0}'.format(name) for name in kwargs.keys()
            )

        query = query.format(
            table,
            ','.join('{0} = :{0}'.format(name) for name in fieldnames),
            where_query
        )

        return self.execute(query, fields)


sys.modules[__name__] = Database()
