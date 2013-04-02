# -*- coding: utf-8 -*-
import importlib
import datetime
import dateutil.parser
from . import connection

class ReadOnlyError(Exception):
    pass
class InvalidValue(Exception):
    pass
class IncompatibleType(Exception):
    pass
class UnknownType(IncompatibleType):
    pass

class LazyLink(object):
    def __init__(self, link):
        self._link = link
        self._descr = None

    def force(self):
        if self._descr is None:
            c = connection.get_default_connection()
            self._descr = c.resource(self._link).get()
        return self._descr

    def __ne__(self, another):
        return self._link != another._link

    def __eq__(self, another):
        return self._link == another._link

class Reference(object):
    def __init__(self, rel_col, link):
        self._ColClass = rel_col
        self._path = link
        self._de = None

    def dereference(self, instance_module):
        if self._de:
            return self._de
        else:
            if isinstance(self._ColClass, basestring):
                try:
                    mod = importlib.import_module('.'.join(self._ColClass.split('.')[:-1]))
                except:
                    mod = instance_module
                _ColClass = getattr(mod, self._ColClass.split('.')[-1])

            class LazyEntity(_ColClass.Entity):
                pass
            LazyEntity.__name__ = _ColClass.Entity.__name__

            b = LazyEntity(pre_filled=LazyLink(self._path))

            def __getattribute__(self, key):
                self.__class__ = _ColClass.Entity
                self._force()
                return self.__getattribute__(key)

            def __setattr__(self, key, value):
                if key == '__class__':
                    return super(LazyEntity, self).__setattr__(key, value)
                else:
                    return self.__setattr__(key, value)

            LazyEntity.__getattribute__ = __getattribute__
            LazyEntity.__setattr__ = __setattr__

            self._de = b
            return b

class SmartField(object):

    def __init__(self, name=None, required=False, default=None, choices=None):
        self.name = name
        self.required = required
        self.default = default
        self.choices = choices

    def has_default(self, instance):
        my_schema = instance.schema()
        return not self.required

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance._data.get(self.name)
        my_schema = instance.schema()

        if isinstance(value, Reference):
            value = value.dereference(importlib.import_module(instance.__module__))
            
        if value is None:
            if self.default is None:
                # TODO
                if my_schema['fields'][self.name].get('related_type') == 'to_one':
                    return None
                value = my_schema['fields'][self.name]['default']
            else:
                value = self.default
            if callable(value):
                value = value()

        return value

    def __set__(self, instance, value):
        my_schema = instance.schema()
        if not instance._unprotect and my_schema['fields'][self.name]['readonly']:
            raise ReadOnlyError, self.name
        else:
            if my_schema['fields'][self.name]['type'] == 'related' and my_schema['fields'][self.name]['related_type'] == 'to_many':
                # ignore backward references collections
                return
            self.validate(instance, value)
            if self.name not in instance._data or instance._data[self.name] != value:
                instance._data[self.name] = value
                if instance._initialized:
                    instance._mark_as_changed(self.name)

    def convert(self, instance, raw_value):
        my_schema = instance.schema()
        allowed_types = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': lambda v: str(v).lower() == 'true',
            'datetime': lambda v: dateutil.parser.parse(v),
        }
        converter = allowed_types[my_schema['fields'][self.name]['type']]
        return converter(raw_value)

    def validate(self, instance, value):
        my_schema = instance.schema()
        allowed_types = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'datetime': datetime.datetime,
        }
        t = my_schema['fields'][self.name]['type']
        if t not in allowed_types:
            raise UnknownType, t
        if not isinstance(value, allowed_types[t]):
            raise InvalidValue, (value, t)

class SingleRelationMixin(object):

    def convert(self, instance, raw_value):
        my_schema = instance.schema()
        t = my_schema['fields'][self.name]['type']
        rel_type = my_schema['fields'][self.name]['related_type']
        if t == 'related' and rel_type == 'to_one':
            if v is None:
                return None
            return Reference(self._rel_col, raw_value)
        else:
            raise IncompatibleType, t

    def validate(self, instance, value):
        my_schema = instance.schema()
        t = my_schema['fields'][self.name]['type']
        if t != 'related':
            raise IncompatibleType, t
        rel_type = my_schema['fields'][self.name]['related_type']
        # TODO: check not for BaseDocument, but for _rel_col compatibility
        if isinstance(value, (Reference, BaseDocument)) or value is None and rel_type == 'to_one':
            return
        else:
            raise InvalidValue, (value, t)

class ForeignField(SmartField, SingleRelationMixin):
    def __init__(self, name=None, required=False, to_collection=None, back_to=None):
        self._rel_col = to_collection
        self._back_to = back_to
        super(ForeignField, self).__init__(name=name, required=required)

class OneToOne(SmartField, SingleRelationMixin):
    def __init__(self, name=None, required=False, to_collection=None):
        self._rel_col = to_collection
        super(OneToOne, self).__init__(name=name, required=required)

class OneToMany(SmartField):
    def __init__(self, name=None, required=False, to_collection=None):
        self._rel_col = to_collection
        super(OneToMany, self).__init__(name=name, required=required)

    def convert(self, instance, raw_value):
        return None

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance._data.get(self.name)
        my_schema = instance.schema()
        if my_schema['fields'][self.name].get('related_type') == 'to_many':
            # TODO: refactor this copy&paste
            mod = importlib.import_module(instance.__module__)
            try:
                mod = importlib.import_module('.'.join(self._ColClass.split('.')[:-1]))
            except:
                mod = mod
            _ColClass = getattr(mod, self._rel_col.split('.')[-1])
            for _, field in _ColClass.Entity._iter_fields():
                if isinstance(field, ForeignField) and field._back_to == self.name:
                    return _ColClass.filter(**{field.name: instance.id})
            raise Exception, 'TODO'
        else:
            return super(OneToMany).__get__(instance, owner)
