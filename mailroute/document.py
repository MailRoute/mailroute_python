# -*- coding: utf-8 -*-
import datetime
import dateutil.parser
from fields import LazyLink, SmartField, OneToMany, OneToOne, ForeignField
from . import connection

class NotActualSchema(Exception):
    pass

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

        if getattr(new_class, 'Meta', None) is not None:
            # handle just only real classes
            for _, field in new_class._iter_fields():
                if isinstance(field, OneToMany):
                    try:
                        new_class.Meta.ignored
                    except:
                        new_class.Meta.ignored = []
                    new_class.Meta.ignored.append(field.name)
            try:
                ignored = set(new_class.Meta.ignored)
            except:
                # there are no ignored field, nothing to do here
                pass
            else:
                for _, field in new_class._iter_fields():
                    if field.name in ignored:
                        field.mark_as_ignored()
        return new_class

class AbstractDocument(object):
    __metaclass__ = DocumentMetaclass

class BaseDocument(AbstractDocument):

    id = SmartField(default=lambda: None)
    uri = SmartField(name='resource_uri', default=lambda: None)

    def __new__(cls, *args, **kwargs):
        if not cls.is_actual():
            raise NotActualSchema, cls
        return AbstractDocument.__new__(cls, *args, **kwargs)

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

    def _force(self):
        if not self._dereferenced:
            self._fill(self.__fill_data.force())
            del self.__fill_data

    def _mark_as_changed(self, fname):
        self._changed.add(fname)

    @classmethod
    def entity_name(cls):
        return cls.Meta.entity_name

    @classmethod
    def _iter_fields(cls, show_ignored=True):
        for basis in cls.__mro__:
            if not issubclass(basis, AbstractDocument):
                continue
            for pname in basis._field_names:
                f_object = getattr(cls, pname)
                if show_ignored or not f_object.ignored:
                    yield pname, f_object

    @classmethod
    def schema(cls):
        c = connection.get_default_connection()
        return c.schema_for(cls.entity_name())['schema']

    @classmethod
    def is_actual(cls):
        my_schema = cls.schema()
        ignored = getattr(cls.Meta, 'ignored', [])
        if set(my_schema['fields']).difference(ignored) == set(field.name for _, field in cls._iter_fields(show_ignored=False)):
            for _, field in cls._iter_fields():
                if not field.is_actual_for(my_schema):
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
