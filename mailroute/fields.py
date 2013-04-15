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

def _resolve_class(class_or_name, instance_module):
    if isinstance(class_or_name, basestring):
        try:
            mod = importlib.import_module('.'.join(class_or_name.split('.')[:-1]))
        except:
            mod = instance_module
        return getattr(mod, class_or_name.split('.')[-1])
    else:
        return class_or_name

class Reference(object):
    def __init__(self, forcing_callback, rel_col, link):
        self._f_callback = forcing_callback
        self._ColClass = rel_col
        self._path = link
        self._de = None

    def dereference(self, instance_module):
        if self._de:
            return self._de
        else:
            _ColClass = _resolve_class(self._ColClass, instance_module)

            class LazyEntity(_ColClass.Entity):
                pass
            LazyEntity.__name__ = _ColClass.Entity.__name__

            b = LazyEntity(pre_filled=LazyLink(self._path))

            ref_self = self
            def __getattribute__(self, key):
                self.__class__ = _ColClass.Entity
                ref_self._f_callback()
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

class Typed(object):

    def is_allowed(self, type_name, options):
        has_store = hasattr(self, 'store_{0}'.format(type_name))
        has_load = hasattr(self, 'load_{0}'.format(type_name))
        return has_store or has_load

    def is_not_allowed(self, type_name, options):
        return not self.is_allowed(type_name, options)

    def convert(self, type_name, value):
        converter = getattr(self, 'load_{0}'.format(type_name))
        return converter(value)

    def is_valid(self, type_name, value):
        need_class = getattr(self, 'store_{0}'.format(type_name))
        if inspect.isfunction(need_class):
            checker = need_class
            return checker(value)
        else:
            if not isinstance(value, need_class):
                return False
            else:
                return True

    def is_not_valid(self, type_name, value):
        return not self.is_valid(type_name, value)

class SmartField(object):

    class Transform(Typed):

        store_string = load_string = str
        store_integer = load_integer = int
        store_float = load_float = float
        store_boolean = bool
        load_boolean = lambda v: str(v).lower() == 'true'
        store_datetime = datetime.datetime
        load_datetime = lambda v: dateutil.parser.parse(v)

    def __init__(self, name=None, required=False, default=None, choices=None):
        self.name = name
        self.required = required
        self.default = default
        self.choices = choices
        self.ignored = False
        self._transformer = self.Transform()

    def mark_as_ignored(self):
        self.ignored = True

    def has_default(self, instance):
        my_schema = instance.schema()
        return not self.required

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance._data.get(self.name)
        my_schema = instance.schema()

        if isinstance(value, Reference):
            # TODO: remove module trick
            value = value.dereference(importlib.import_module(instance.__module__))
            
        if value is None:
            if not my_schema['fields'][self.name]['nullable']:
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
        elif my_schema['fields'][self.name]['nullable'] and value is None:
            # TODO: copy&paste
            instance._data[self.name] = value
            instance._mark_as_changed(self.name)
        else:
            self.validate(instance, value)
            if self.name not in instance._data or instance._data[self.name] != value:
                instance._data[self.name] = value
                instance._mark_as_changed(self.name)

    def convert(self, instance, raw_value):
        my_schema = instance.schema()
        # TODO: copy&paste
        if my_schema['fields'][self.name]['nullable'] and raw_value is None:
            return None
        else:
            return self._transformer.convert(my_schema['fields'][self.name]['type'], raw_value)

    def validate(self, instance, value):
        my_schema = instance.schema()
        options = my_schema['fields'][self.name]
        vtype = options['type']
        if self._transformer.is_not_allowed(vtype, options):
            raise UnknownType, vtype
        if self._transformer.is_not_valid(vtype, value):
            raise InvalidValue, (value, vtype)

    def is_actual_for(self, schema):
        options = schema['fields'].get(self.name, {})
        if not self.ignored:
            return self._transformer.is_allowed(options.get('type'), options)
        else:
            return True

class SingleRelation(SmartField):

    class Transform(Typed):

        def load_related(self, raw_value):
            if raw_value is None:
                return None
            else:
                return Reference(lambda: instance._force(self.name), self._rel_col, raw_value)

        def store_related(self, value):
            mod = importlib.import_module(instance.__module__)
            _ColClass = _resolve_class(self._rel_col, mod)
            if isinstance(value, (Reference, _ColClass.Entity)):
                return True
            elif value is None:
                return True
            else:
                return False

        def is_actual_for(self, type_name, options):
            parent_approves = super(self, SingleRelation.Transform).is_actual_for(type_name, options)
            if parent_approves and options.get('related_type') == 'to_one':
                return True
            else:
                return False

class ForeignField(SingleRelation):
    def __init__(self, name=None, required=False, to_collection=None, back_to=None):
        self._rel_col = to_collection
        self._back_to = back_to
        super(ForeignField, self).__init__(name=name, required=required, default=lambda: None)

class OneToOne(SingleRelation):
    def __init__(self, name=None, required=False, to_collection=None):
        self._rel_col = to_collection
        super(OneToOne, self).__init__(name=name, required=required, default=lambda: None)

class OneToMany(SmartField):

    class Transform(Typed):

        def load_related(self, raw_value):
            return None

        def is_actual_for(self, type_name, options):
            parent_approves = super(self, OneToMany.Transform).is_actual_for(type_name, options)
            if parent_approves and options.get('related_type') == 'to_many':
                return True
            else:
                return False

    def __init__(self, name=None, required=False, to_collection=None):
        self._rel_col = to_collection
        super(OneToMany, self).__init__(name=name, required=required)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance._data.get(self.name)
        my_schema = instance.schema()
        # TODO: refactor this copy&paste
        mod = importlib.import_module(instance.__module__)
        _ColClass = _resolve_class(self._rel_col, mod)
        # TODO: improve performance
        for _, field in _ColClass.Entity._iter_fields():
            if isinstance(field, ForeignField) and field._back_to == self.name:
                return _ColClass.filter(**{field.name: instance.id})
        raise Exception, 'TODO: Backward field is not found'

    def __set__(self, instance, value):
        # ignore backward references collections
        if instance._unprotect:
            return
        else:
            raise ReadOnlyError, self.name
