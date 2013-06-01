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
class ReferenceIssue(Exception):
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

class Resolver(object):

    def __init__(self, ctx):
        self._instance_module = importlib.import_module(ctx.__module__)

    def find_class(self, class_or_name):
        if isinstance(class_or_name, basestring):
            try:
                mod = importlib.import_module('.'.join(class_or_name.split('.')[:-1]))
            except:
                mod = self._instance_module
            return getattr(mod, class_or_name.split('.')[-1])
        else:
            return class_or_name

    def find_entity_class(self, class_or_name):
        return self.find_class(class_or_name).Entity

class Reference(object):
    def __init__(self, forcing_callback, rel_col, link):
        self._f_callback = forcing_callback
        self._name_or_class = rel_col
        self._path = link
        self._de = None

    def dereference(self, linker):
        if self._de:
            return self._de
        else:
            EntityClass = linker.find_entity_class(self._name_or_class)

            class LazyEntity(EntityClass):
                pass
            LazyEntity.__name__ = EntityClass.__name__

            b = LazyEntity(pre_filled=LazyLink(self._path))

            ref_self = self
            def __getattribute__(self, key):
                if key.startswith('_'):
                    return EntityClass.__getattribute__(self, key)
                else:
                    self.__class__ = EntityClass
                    self._force()
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

    def __init__(self, for_instance):
        self._instance = for_instance

    @classmethod
    def is_allowed(cls, type_name, options):
        has_store = hasattr(cls, 'store_{0}'.format(type_name))
        has_load = hasattr(cls, 'load_{0}'.format(type_name))
        return has_store or has_load

    def is_not_allowed(self, type_name, options):
        return not self.is_allowed(type_name, options)

    def convert(self, type_name, value):
        converter = getattr(self, 'load_{0}'.format(type_name))
        return converter(value)

    def is_valid(self, type_name, value):
        need_class = getattr(self, 'store_{0}'.format(type_name))
        if inspect.isfunction(need_class) or inspect.ismethod(need_class):
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
        load_boolean = lambda self, v: str(v).lower() == 'true'
        store_datetime = datetime.datetime
        load_datetime = lambda self, v: dateutil.parser.parse(v)

    def __init__(self, name=None, required=False, default=None, choices=None, nullable=False, readonly=False):
        self.name = name
        self.required = required
        self.default = default
        self.choices = choices
        self.ignored = False
        self.nullable = nullable
        self.readonly = readonly

    def _transformer(self, for_instance):
        return self.Transform(for_instance)

    def mark_as_ignored(self):
        self.ignored = True

    def has_default(self, instance):
        my_schema = instance.schema()
        return not self.required

    def has_nullable(self, instance):
        my_schema = instance.schema()
        if self.name not in my_schema['fields']:
            return self.nullable
        else:
            return my_schema['fields'][self.name].get('nullable', False) or self.nullable

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance._data.get(self.name)
        my_schema = instance.schema()

        if isinstance(value, Reference):
            value = value.dereference(linker=Resolver(instance))
            
        if value is None:
            if not self.has_nullable(instance):
                if self.default is None:
                    value = my_schema['fields'][self.name]['default']
                else:
                    value = self.default
            if callable(value):
                value = value()

        return value

    def _save(self, instance, value):
        instance._data[self.name] = value
        instance._mark_as_changed(self.name)

    def __set__(self, instance, value):
        my_schema = instance.schema()
        if not instance._unprotect and (my_schema['fields'][self.name]['readonly'] or self.readonly):
            raise ReadOnlyError, self.name
        elif self.has_nullable(instance) and value is None:
            self._save(instance, value)
        else:
            self.validate(instance, value)
            if self.name not in instance._data or instance._data[self.name] != value:
                self._save(instance, value)

    def convert(self, instance, raw_value):
        my_schema = instance.schema()
        if self.has_nullable(instance) and raw_value is None:
            return None
        else:
            return self._transformer(instance).convert(my_schema['fields'][self.name]['type'], raw_value)

    def validate(self, instance, value):
        my_schema = instance.schema()
        options = my_schema['fields'][self.name]
        vtype = options['type']
        tsr = self._transformer(instance)
        if tsr.is_not_allowed(vtype, options):
            raise UnknownType, vtype
        if tsr.is_not_valid(vtype, value):
            raise InvalidValue, (value, vtype)

    def is_actual_for(self, schema):
        options = schema['fields'].get(self.name, {})
        if not self.ignored:
            return self.Transform.is_allowed(options.get('type'), options)
        else:
            return True

class AbstractRelation(SmartField):

    def find_class(self, context):
        return Resolver(context).find_class(self._rel_col)

    def find_entity_class(self, context):
        return Resolver(context).find_entity_class(self._rel_col)

class SingleRelation(AbstractRelation):

    def _transformer(self, for_instance):
        rfactory = lambda raw_value: Reference(lambda: for_instance._mark_as_forced(self.name), self._rel_col, raw_value)
        EntityClass = self.find_entity_class(for_instance) # TODO: here should be field owner context
        return self.Transform(for_instance, EntityClass, rfactory)

    class Transform(Typed):

        def __init__(self, for_instance, EntityClass, ref_factory):
            super(SingleRelation.Transform, self).__init__(for_instance)
            self._ref_factory = ref_factory
            self._EntityClass = EntityClass

        def load_related(self, raw_value):
            if raw_value is None:
                return None
            else:
                return self._ref_factory(raw_value)

        def store_related(self, value):
            if isinstance(value, (Reference, self._EntityClass)):
                return True
            elif value is None:
                return True
            else:
                return False

        @classmethod
        def is_allowed(cls, type_name, options):
            parent_approves = super(cls, SingleRelation.Transform).is_allowed(type_name, options)
            if parent_approves and options.get('related_type') == 'to_one':
                return True
            else:
                return False

class ForeignField(SingleRelation):
    def __init__(self, name=None, required=False, to_collection=None, back_to=None):
        self._rel_col = to_collection
        self._back_to = back_to
        super(ForeignField, self).__init__(name=name, required=required, default=lambda: None, nullable=True)

class OneToOne(SingleRelation):
    def __init__(self, name=None, required=False, to_collection=None):
        self._rel_col = to_collection
        super(OneToOne, self).__init__(name=name, required=required, default=lambda: None, nullable=True)

class OneToMany(AbstractRelation):

    class Transform(Typed):

        def load_related(self, raw_value):
            return None

        @classmethod
        def is_allowed(cls, type_name, options):
            parent_approves = super(cls, OneToMany.Transform).is_allowed(type_name, options)
            if parent_approves and options.get('related_type') == 'to_many':
                return True
            else:
                return False

    def __init__(self, name=None, required=False, to_collection=None):
        self._rel_col = to_collection
        super(OneToMany, self).__init__(name=name, required=required)

    def _new_query(self, owner, ColClass, field_name, instance):
        return ColClass.filter(**{field_name: instance.id})

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance._data.get(self.name)
        my_schema = instance.schema()
        ColClass = self.find_class(owner)
        # TODO: improve performance
        for _, field in ColClass.Entity._iter_fields():
            # TODO: it's possible that find entity class uses wrong owner
            if isinstance(field, ForeignField) and field._back_to == self.name and field.find_entity_class(owner) == owner:
                return self._new_query(owner, ColClass, field.name, instance)
        raise ReferenceIssue, ('Backward field {0} is not found in the {1}'.format(self.name, ColClass),)

    def __set__(self, instance, value):
        # ignore backward references collections
        if instance._unprotect:
            return
        else:
            raise ReadOnlyError, self.name

    def convert(self, instance, raw_value):
        # ignore any loaded values from object for one -> many relation
        return []

class VirtualOneToMany(OneToMany):

    def _new_query(self, owner, ColClass, field_name, instance):
        return ColClass(owner.entity_name(), instance.id)
