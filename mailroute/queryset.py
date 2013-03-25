# -*- coding: utf-8 -*-
from . import connection

class DoesNotExist(Exception):
    pass


class MultipleObjectsReturned(Exception):
    pass


class InvalidQueryError(Exception):
    pass


class InvalidFilter(InvalidQueryError):
    pass

class InvalidOrder(InvalidQueryError):
    pass

class OperationError(Exception):
    pass


class NotUniqueError(OperationError):
    pass


class QuerySet(object):

    def __init__(self, filters={}):
        self._filters = filters
        self._cached = None

    @classmethod
    def entity_name(cls):
        return cls.Entity.entity_name()

    @classmethod
    def get(cls, id):
        c = connection.get_default_connection()
        o = cls.Entity(pre_filled=c.objects(cls.entity_name()).one(id).get())
        return o

    @classmethod
    def create(cls, **initial):
        o = cls.Entity(pre_filled=initial)
        o.save()
        return o

    @classmethod
    def bulk_create(cls, descriptions):
        for initial in descriptions:
            cls.create(**initial)

    @classmethod
    def all(cls):
        return cls()

    @classmethod
    def filter(cls, **options):
        return cls(filters=options)

    @classmethod
    def delete(cls, resources):
        c = connection.get_default_connection()
        for entity in resources:
            if isinstance(entity, (basestring, int)):
                oid = str(entity)
                c.objects(cls.entity_name()).one(oid).delete()
            else:
                entity.delete()

    # DON'T MAKE THIS METHODS (limit & offset) as classmethods
    def limit(self, num):
        f = dict(self._filters)
        f['limit'] = num
        return self.__class__(filters=f)

    def offset(self, num):
        f = dict(self._filters)
        f['offset'] = num
        return self.__class__(filters=f)

    def order_by(self, rule):
        f = dict(self._filters)
        f['order_by'] = rule
        # TODO: check allowed fields for ordering
        return self.__class__(filters=f)

    def fetch(self):
        return list(self)

    def __bool__(self):
        return len(self) > 0

    def __nonzero__(self):
        return len(self) > 0

    def __len__(self):
        if self._cached is not None:
            return len(self._cached['objects'])
        else:
            return sum(1 for _ in self)

    def __getitem__(self, ind):
        if isinstance(ind, slice):
            if self._cached is not None:
                infos = self._cached['objects'][ind]
                objs = []
                for info in infos:
                    o = self.__class__.Entity(pre_filled=info)
                    objs.append(o)
                return objs
            else:
                return self.fetch()[ind]
        else:
            if self._cached is not None:
                info = self._cached['objects'][ind]
                o = self.__class__.Entity(pre_filled=info)
                return o
            else:
                return self.fetch()[ind]

    def __iter__(self):
        if self._cached is None:
            c = connection.get_default_connection()
            self._cached = ans = c.objects(self.entity_name()).get(**self._filters)
        else:
            ans = self._cached

        for info in ans['objects']:
            o = self.__class__.Entity(pre_filled=info)
            yield o
