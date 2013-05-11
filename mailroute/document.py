# -*- coding: utf-8 -*-
import datetime
import dateutil.parser
from contextlib import contextmanager
from fields import LazyLink, SmartField, OneToMany, OneToOne, ForeignField
from . import connection

class DoesNotExist(Exception):
    pass

class NotActualSchema(Exception):
    pass

class InitializationError(Exception):
    pass

class DocumentMetaclass(type):

    def __new__(cls, name, bases, attrs):
        # if a base class just call super
        metaclass = attrs.get('my_metaclass')
        super_new = super(DocumentMetaclass, cls).__new__

        if metaclass and issubclass(metaclass, DocumentMetaclass):
            return super_new(cls, name, bases, attrs)

        attrs['_field_names'] = cls.sieved_fields(attrs)

        # create the new_class
        new_class = super_new(cls, name, bases, attrs)
        cls.update_ignored(new_class)
        return new_class

    @classmethod
    def sieved_fields(cls, attrs):
        _fields = []
        for fname, field in attrs.iteritems():
            if not isinstance(field, SmartField):
                continue
            if field.name is None:
                field.name = fname
            _fields.append(fname)
        return _fields

    @classmethod
    def update_ignored(cls, new_class):
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

class AbstractDocument(object):
    __metaclass__ = DocumentMetaclass

class BaseDocument(AbstractDocument):

    id = SmartField(default=lambda: None, nullable=True, readonly=True)
    uri = SmartField(name='resource_uri', default=lambda: None)

    def __new__(cls, *args, **kwargs):
        if not cls.is_actual():
            raise NotActualSchema, cls
        return AbstractDocument.__new__(cls, *args, **kwargs)

    def __init__(self, pre_filled=None):
        with self._just_reloaded():
            self._data = {}
            self._unprotect = False
            self._dereferenced = True
            if pre_filled and isinstance(pre_filled, dict):
                with self._disabled_protection():
                    self._fill(pre_filled)
            elif isinstance(pre_filled, LazyLink):
                self._dereferenced = False
                self.__fill_data = pre_filled
            else:
                self._initialized = True

    @contextmanager
    def _just_reloaded(self):
        self._initialized = False
        self._changed = set()
        self._forced = set()
        yield
        pass

    def _mark_as_forced(self, for_fname):
        self._forced.add(for_fname)

    def _force(self):
        if not self._dereferenced:
            with self._disabled_protection():
                self._fill(self.__fill_data.force())
            del self.__fill_data

    def _mark_as_changed(self, fname):
        if self._initialized:
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
        schema_descr = set(my_schema['fields']).difference(ignored)
        class_descr = set(field.name for _, field in cls._iter_fields(show_ignored=False))
        if schema_descr == class_descr:
            # check type for each field
            for _, field in cls._iter_fields():
                if not field.is_actual_for(my_schema):
                    return False
            return True
        else:
            return False

    def _save_children(self):
        for pname, field in self._iter_fields():
            nested = getattr(self, pname)
            if field.name in self._forced and isinstance(nested, BaseDocument):
                nested.save()

    def _changed_to_dict(self):
        new_values = {}

        for pname, field in self._iter_fields():
            fname = field.name
            if fname in self._changed:
                new_values[fname] = getattr(self, pname)
        return new_values

    def save(self):
        self._save_children()

        if not self._changed:
            return

        new_values = self._changed_to_dict()
        c = connection.get_default_connection()
        if self.id is None:             # has never been saved before
            res = c.objects(self.entity_name()).create(new_values)
        else:
            res = c.resource(self.uri).update(new_values)
        with self._just_reloaded():
            with self._disabled_protection():
                self._fill(res)

    def delete(self):
        if self.id is not None:
            c = connection.get_default_connection()
            try:
                c.resource(self.uri).delete()
            except connection.NotFound:
                raise DoesNotExist, self.id
            with self._disabled_protection():
                self.id = None
            return True
        else:
            return False

    @contextmanager
    def _disabled_protection(self):
        old_state = self._unprotect
        self._unprotect = True
        yield old_state
        self._unprotect = False

    def _fill(self, raw_source):
        my_schema = self.schema()

        for pname, cls_field in self._iter_fields():
            fname = cls_field.name
            try:
                value = raw_source[fname]
            except KeyError:
                if not cls_field.has_default(instance=self):
                    raise InitializationError, cls_field.name
            else:
                setattr(self, pname, cls_field.convert(self, value))
        self._initialized = True
        self._dereferenced = True

    def __ne__(self, another):
        return not (self == another)

    def __eq__(self, another):
        if isinstance(another, BaseDocument):
            if not self._dereferenced and not another._dereferenced:
                return self.__fill_data == another.__fill_data
            else:
                for pname, field in self._iter_fields():
                    # TODO: make this condition better not so rough
                    if getattr(self, pname) != getattr(another, pname) and not isinstance(field, OneToMany):
                        return False
                return True
        else:
            return False

    def __serialize__(self):
        return self.uri

class BaseCreatableDocument(BaseDocument):
    created_at = SmartField(default=datetime.datetime.now)
    updated_at = SmartField(default=datetime.datetime.now)
