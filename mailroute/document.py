# -*- coding: utf-8 -*-
import datetime
import dateutil.parser

class ReadOnlyError(Exception):
    pass
class InvalidValue(Exception):
    pass
class UnknownType(Exception):
    pass

# class BasesTuple(tuple):
#     """Special class to handle introspection of bases tuple in __new__"""
#     pass


# class BaseList(list):
#     """A special list so we can watch any changes
#     """

#     _dereferenced = False
#     _instance = None
#     _name = None

#     def __init__(self, list_items, instance, name):
#         self._instance = weakref.proxy(instance)
#         self._name = name
#         return super(BaseList, self).__init__(list_items)

#     def __setitem__(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseList, self).__setitem__(*args, **kwargs)

#     def __delitem__(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseList, self).__delitem__(*args, **kwargs)

#     def __getstate__(self):
#         self.observer = None
#         return self

#     def __setstate__(self, state):
#         self = state
#         return self

#     def append(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseList, self).append(*args, **kwargs)

#     def extend(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseList, self).extend(*args, **kwargs)

#     def insert(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseList, self).insert(*args, **kwargs)

#     def pop(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseList, self).pop(*args, **kwargs)

#     def remove(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseList, self).remove(*args, **kwargs)

#     def reverse(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseList, self).reverse(*args, **kwargs)

#     def sort(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseList, self).sort(*args, **kwargs)

#     def _mark_as_changed(self):
#         if hasattr(self._instance, '_mark_as_changed'):
#             self._instance._mark_as_changed(self._name)


# class BaseDict(dict):
#     """A special dict so we can watch any changes
#     """

#     _dereferenced = False
#     _instance = None
#     _name = None

#     def __init__(self, dict_items, instance, name):
#         self._instance = weakref.proxy(instance)
#         self._name = name
#         return super(BaseDict, self).__init__(dict_items)

#     def __setitem__(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseDict, self).__setitem__(*args, **kwargs)

#     def __delete__(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseDict, self).__delete__(*args, **kwargs)

#     def __delitem__(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseDict, self).__delitem__(*args, **kwargs)

#     def __delattr__(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseDict, self).__delattr__(*args, **kwargs)

#     def __getstate__(self):
#         self.instance = None
#         self._dereferenced = False
#         return self

#     def __setstate__(self, state):
#         self = state
#         return self

#     def clear(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseDict, self).clear(*args, **kwargs)

#     def pop(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseDict, self).pop(*args, **kwargs)

#     def popitem(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseDict, self).popitem(*args, **kwargs)

#     def update(self, *args, **kwargs):
#         self._mark_as_changed()
#         return super(BaseDict, self).update(*args, **kwargs)

#     def _mark_as_changed(self):
#         if hasattr(self._instance, '_mark_as_changed'):
#             self._instance._mark_as_changed(self._name)

class Reference(object):
    def __init__(self, Class, link):
        self._ColClass = Class
        self._link = link
        self._de = None

    def dereference(self):
        if self._de:
            return self._de
        else:
            # TODO: refactor this!!!!
            import connection
            descr = connection._default_connection._grab(connection._default_connection._server(self._link))
            b = self._ColClass.Entity()              # TODO: some common class instead branding
            b._fill(descr)
            self._de = b
            return b

class SmartField(object):

    def __init__(self, name=None, required=False, default=None, to_collection=None):
        self.name = name
        self.required = required
        self.default = default
        self._rel_col = to_collection

    def has_default(self, instance):
        my_schema = self._get_schema(instance)
        return not self.required

    def _get_schema(self, instance):
        # TODO: refactor this
        import connection
        descr = connection._default_connection.schema_for(instance.Meta.entity_name)
        my_schema = descr['schema']
        return my_schema

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance._data.get(self.name)
        if isinstance(value, Reference):
            value = value.dereference()
            print value
            
        if value is None:
            if self.default is None:
                my_schema = self._get_schema(instance)
                value = my_schema['fields'][self.name]['default']
            else:
                value = self.default
            if callable(value):
                value = value()

        return value

    def __set__(self, instance, value):
        my_schema = self._get_schema(instance)
        if not instance._unprotect and my_schema['fields'][self.name]['readonly']:
            raise ReadOnlyError, self.name
        else:
            if self.name not in instance._data or instance._data[self.name] != value:
                instance._data[self.name] = value
                if instance._initialized:
                    instance._mark_as_changed(self.name)

    def validate(self, value):
        my_schema = self._get_schema(instance)
        allowed_types = {
            'string': str,
            'integer': int,
            'boolean': bool,
            'datetime': datetime.datetime,
            'related': BaseDocument,    # TODO: check real class
        }
        t = my_schema['fields'][self.name]['type']
        if t not in allowed_types:
            raise UnknownType, t
        if not isinstance(value, allowed_types[t]):
            raise InvalidValue, (value, t)


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

class BaseDocument(object):

    __metaclass__ = DocumentMetaclass

    id = SmartField(default=lambda: None)
    uri = SmartField(name='resource_uri', default=lambda: None)
    created_at = SmartField(default=datetime.datetime.now)
    updated_at = SmartField(default=datetime.datetime.now)

    def __init__(self):
        self._data = {}
        self._initialized = True
        self._unprotect = False
        self._changed = set()

    def _mark_as_changed(self, fname):
        self._changed.add(fname)

    @classmethod
    def _iter_fields(cls):
        for basis in cls.__mro__:
            if not issubclass(basis, BaseDocument):
                continue
            for pname in basis._field_names:
                yield pname, getattr(cls, pname)

    @classmethod
    def schema(cls):
        import connection
        c = connection._default_connection
        return c.schema_for(cls.Meta.entity_name)

    @classmethod
    def is_actual(cls):
        my_schema = cls.schema()['schema']
        return set(my_schema['fields']) == set(field.name for _, field in cls._iter_fields())

    def save(self):
        if not self._changed:           # TODO: check children!!!!!!!
            return
        new_values = {}
        for basis in self.__class__.__mro__:
            if not issubclass(basis, BaseDocument):
                continue
            for pname in basis._field_names:
                field = getattr(self.__class__, pname)
                fname = field.name
                if not field.has_default(instance=self) and fname in self._changed:
                    new_values[fname] = getattr(self, pname)
        import connection
        c = connection._default_connection
        if self.id is None:
            res = c._send(c._objects(self.Meta.entity_name), new_values)
        else:
            res = c._update(c._object_id(self.Meta.entity_name, self.id), new_values)
        print res
        self._fill(res)
        self._changed = set()

    def delete(self):
        import connection
        c = connection._default_connection
        c._remove(c._server(self.uri))
        return True

    def _fill(self, raw_source):
        self._initialized = False
        self._unprotect = True
        # TODO: refactor this
        import connection
        descr = connection._default_connection.schema_for(self.Meta.entity_name)
        my_schema = descr['schema'] 

        allowed_types = {
            'string': str,
            'integer': int,
            'boolean': lambda v: str(v).lower() == 'true',
            'datetime': lambda v: dateutil.parser.parse(v),
            'related': lambda v: Reference(v), # TODO: try to create necessary class
        }
        for basis in self.__class__.__mro__:
            if not issubclass(basis, BaseDocument):
                continue
            for pname in basis._field_names:
                fname = getattr(self.__class__, pname).name
                converter = allowed_types[my_schema['fields'][fname]['type']]
                try:
                    value = raw_source[fname]
                    setattr(self, pname, converter(value))
                except KeyError:
                    pass
        self._initialized = True
        self._unprotect = False
