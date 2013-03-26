# -*- coding: utf-8 -*-
import inspect
import importlib
import datetime
import dateutil.parser
from . import connection

class ReadOnlyError(Exception):
    pass
class InvalidValue(Exception):
    pass
class UnknownType(Exception):
    pass

class LazyLink(object):
    def __init__(self, link):
        self._link = link

    def force(self):
        # TODO: refactor this!!!!
        c = connection.get_default_connection()
        descr = c.resource(self._link).get()

    def __ne__(self, another):
        return self._link != another._link

    def __eq__(self, another):
        return self._link == another._link

class Reference(object):
    def __init__(self, FieldClass, link):
        self._ColClass = FieldClass._rel_col
        self._FieldClass = FieldClass
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
            b = _ColClass.Entity(pre_filled=LazyLink(self._path))
            self._de = b
            return b

class SmartField(object):

    def __init__(self, name=None, required=False, default=None):
        self.name = name
        self.required = required
        self.default = default

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
        # TODO: refactor
        my_schema = instance.schema()
        allowed_types = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': lambda v: str(v).lower() == 'true',
            'datetime': lambda v: dateutil.parser.parse(v),
            'related': lambda cls_field, v: Reference(cls_field, v), # TODO: try to create necessary class
        }
        converter = allowed_types[my_schema['fields'][self.name]['type']]
        if not inspect.isfunction(converter) or len(inspect.getargspec(converter).args) == 1:
            return converter(raw_value)
        else:
            return converter(self, raw_value)

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
            if t != 'related':
                raise UnknownType, t
            else:
                if isinstance(value, (Reference, BaseDocument)):
                    return
                else:
                    raise InvalidValue, (value, t)
        if not isinstance(value, allowed_types[t]):
            raise InvalidValue, (value, t)

class ForeignField(SmartField):
    def __init__(self, name=None, required=False, to_collection=None, back_to=None):
        self._rel_col = to_collection
        self._back_to = back_to
        super(ForeignField, self).__init__(name=name, required=required)

class OneToOne(SmartField):
    def __init__(self, name=None, required=False, to_collection=None):
        self._rel_col = to_collection
        super(OneToOne, self).__init__(name=name, required=required)

class OneToMany(SmartField):
    def __init__(self, name=None, required=False, to_collection=None):
        self._rel_col = to_collection
        super(OneToMany, self).__init__(name=name, required=required)

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

class DocumentMetaclass(type):

    def __new__(cls, name, bases, attrs):
        # If a base class just call super
        metaclass = attrs.get('my_metaclass')
        super_new = super(DocumentMetaclass, cls).__new__

        if metaclass and issubclass(metaclass, DocumentMetaclass):
            return super_new(cls, name, bases, attrs)

        _fields = []
        for fname, field in attrs.iteritems():
            if not isinstance(field, SmartField):
                continue
            if field.name is None:
                field.name = fname
            _fields.append(fname)

        attrs['_field_names'] = _fields

        # Create the new_class
        new_class = super_new(cls, name, bases, attrs)
        return new_class

class AbstractDocument(object):
    __metaclass__ = DocumentMetaclass

class BaseDocument(AbstractDocument):

    id = SmartField(default=lambda: None)
    uri = SmartField(name='resource_uri', default=lambda: None)

    def __init__(self, pre_filled=None):
        self._data = {}
        self._initialized = True
        self._unprotect = False
        self._dereferenced = True
        if pre_filled and isinstance(pre_filled, dict):
            self._fill(pre_filled)
            self._changed = set(pre_filled.keys())
        elif isinstance(pre_filled, LazyLink):
            self._dereferenced = False
            self.__fill_data = pre_filled
            self._changed = set()
        else:
            self._changed = set()

    # def __getattribute__(self, key):
    #     if key != '_dereferenced' and not self._dereferenced:
    #         self._dereferenced = True
    #         pre_filled = self.__fill_data.force()
    #         self._fill(pre_filled)
    #         self._changed = set(pre_filled.keys())
    #         del self.__fill_data
    #     return super(BaseDocument, self).__getattribute__(key)

    # def __setattr__(self, key, value):
    #     self.__fill_data
    #     return AbstractDocument.__setattr__(self, key, value)

    def _mark_as_changed(self, fname):
        self._changed.add(fname)

    @classmethod
    def entity_name(cls):
        return cls.Meta.entity_name

    @classmethod
    def _iter_fields(cls):
        for basis in cls.__mro__:
            if not issubclass(basis, AbstractDocument):
                continue
            for pname in basis._field_names:
                yield pname, getattr(cls, pname)

    @classmethod
    def schema(cls):
        c = connection.get_default_connection()
        return c.schema_for(cls.entity_name())['schema']

    @classmethod
    def is_actual(cls):
        my_schema = cls.schema()
        ignored = getattr(cls.Meta, 'ignored', [])
        if set(my_schema['fields']).difference(ignored) == set(field.name for _, field in cls._iter_fields()).difference(ignored):
            for _, field in cls._iter_fields():
                # TODO: refactor this
                if my_schema['fields'][field.name].get('related_type') == 'to_many' and not isinstance(field, OneToMany):
                    return False
            return True
        else:
            return False

    def save(self):
        if not self._changed:           # TODO: check children!!!!!!!
            return
        new_values = {}
        for pname, field in self._iter_fields():
            fname = field.name
            if not field.has_default(instance=self) and fname in self._changed:
                new_values[fname] = getattr(self, pname)
        c = connection.get_default_connection()
        if self.id is None:
            res = c.objects(self.entity_name()).create(new_values)
        else:
            res = c.objects(self.entity_name()).one(self.id).update(new_values)
        self._fill(res)
        self._changed = set()

    def delete(self):
        c = connection.get_default_connection()
        c.resource(self.uri).delete()
        return True

    def _fill(self, raw_source):
        # TODO: refactor this
        self._initialized = False
        self._unprotect = True
        my_schema = self.schema()

        for pname, cls_field in self._iter_fields():
            fname = cls_field.name
            try:
                value = raw_source[fname]
            except KeyError:
                if not cls_field.has_default(instance=self):
                    raise
            else:
                setattr(self, pname, cls_field.convert(self, value))
        self._initialized = True
        self._unprotect = False
        self._dereferenced = True

    def __ne__(self, another):
        return not (self == another)

    def __eq__(self, another):
        if not self._dereferenced and not another._dereferenced:
            return self.__fill_data == another.__fill_data
        for pname, field in self._iter_fields():
            if getattr(self, pname) != getattr(another, pname):
                return False
        return True

class BaseCreatableDocument(BaseDocument):
    created_at = SmartField(default=datetime.datetime.now)
    updated_at = SmartField(default=datetime.datetime.now)
