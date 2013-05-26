# -*- coding: utf-8 -*-
import itertools
from . import connection

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

class DeleteError(OperationError):
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
    def _resource_point(cls):
        c = connection.get_default_connection()
        return c.objects(cls.entity_name())

    @classmethod
    def get(cls, id):
        o = cls.Entity(pre_filled=cls._resource_point().one(id).get())
        return o

    @classmethod
    def create(cls, **initial):
        o = cls.Entity()
        # because we really want to mark fields to be changed in this case
        for pname, value in initial.iteritems():
            setattr(o, pname, value)
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
    def search(cls, pattern):
        return cls(filters=dict(q=pattern))

    @classmethod
    def delete(cls, resources):
        issues = []
        for entity in resources:
            if isinstance(entity, (basestring, int)):
                oid = str(entity)
                try:
                    self._resource_point().one(oid).delete()
                except connection.NotFound, e:
                    issues.append((oid, e))
            else:
                try:
                    entity.delete()
                except Exception, e:
                    issues.append((entity, e))
        if issues:
            raise DeleteError, (issues,)

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
            return int(self._cached['meta']['total_count'])
        else:
            lazy_fetch = iter(self)
            try:
                lazy_fetch.next()
            except StopIteration:
                pass
            return int(self._cached['meta']['total_count'])

    def __getitem__(self, ind):
        if isinstance(ind, slice):
            if self._cached is not None or ind.stop is None:
                return itertools.islice(self, ind.start, ind.stop, ind.step)
            else:
                start, stop = ind.start or 0, ind.stop or 0
                if start:
                    query = self.offset(start)
                else:
                    query = self
                return query.limit(stop - start).fetch()
        else:
            self._cache_until(ind)
            info = self._cached['objects'][ind]
            o = self.__class__.Entity(pre_filled=info)
            return o

    def _cache_until(self, ind):
        if len(self) > ind:
            pass
        else:
            # TODO: improve performance, combine code with __iter__
            for i, _ in enumerate(self):
                if i >= ind:
                    return

    def __iter__(self):
        c = connection.get_default_connection()
        if self._cached is None:
            self._cached = ans = self._resource_point().get(**self._filters)
        else:
            ans = self._cached

        while True:
            for info in ans['objects']:
                o = self.__class__.Entity(pre_filled=info)
                yield o

            if not self._cached['meta']['next']:
                break

            next_piece_url = self._cached['meta']['next']
            ans = c.resource(next_piece_url).get()

            self._cached['meta'] = ans['meta']
            self._cached['objects'].extend(ans['objects'])

class VirtualQuerySet(QuerySet):

    def __init__(self, linked_entity_name, main_id, **kwargs):
        super(VirtualQuerySet, self).__init__(**kwargs)
        self._lnk_ename = linked_entity_name
        self._main_id = main_id

    # TODO: parent has classmethod, but here we specify object method
    def _resource_point(self):
        c = connection.get_default_connection()
        return c.objects(self.entity_name()).sub(self._lnk_ename, self._main_id)
