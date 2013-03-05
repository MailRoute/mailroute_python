# -*- coding: utf-8 -*-
from queryset import QuerySet, QNode

class BaseDocument(QNode):

    def __init__(self):
        pass

    def save(self):
        pass

    def delete(self):
        pass

    def __getattribute__(self, name):
        # TODO: refactor this
        import connection
        descr = connection._default_connection.schema_for(object.__getattribute__(self, 'Meta').entity_name)
        my_schema = descr['schema'] 
        if name in my_schema['fields'] and name not in object.__getattribute__(self, 'Meta').required:
            return my_schema['fields'][name]['default']
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        # TODO: refactor this
        import datetime
        import connection
        descr = connection._default_connection.schema_for(object.__getattribute__(self, 'Meta').entity_name)
        my_schema = descr['schema'] 

        allowed_types = {
            'string': str,
            'integer': int,
            'boolean': lambda v: str(v).lower() == 'true',
            'datetime': lambda v: datetime.datetime.strptime(v, '%Y-%m-%dT%H:%M:%S'),
        }
        try:
            super(BaseDocument, self).__setattr__(name, allowed_types[my_schema['fields'][name]['type']](value))
        except ValueError:
            assert 0, 'TODO: custom exception'

class Reseller(BaseDocument):
    class Meta:
        entity_name = 'reseller'
        required = ['name',]
