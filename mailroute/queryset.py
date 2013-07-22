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

        def all():
            return self.__class__(filters=self._filters)
        self.all = all


    @classmethod
    def _make_instance(cls, *args, **kwargs):
        return cls.Entity(*args, **kwargs)

    @classmethod
    def entity_name(cls):
        return cls.Entity.entity_name()

    @classmethod
    def _resource_point(cls):
        c = connection.get_default_connection()
        return c.objects(cls.entity_name())

    @classmethod
    def get(cls, id):
        o = cls._make_instance(pre_filled=cls._resource_point().one(id).get())
        return o

    @classmethod
    def create(cls, **initial):
        o = cls._make_instance()
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
        for field_rule in options:
            field_name = field_rule.split('__')[0]
            if not cls.Entity.allowed_to_filter_by(field_name):
                raise InvalidFilter, field_name
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
                    cls._resource_point().one(oid).delete()
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
        if 'limit' in f:
            f['limit'] = min(f['limit'], num)
        else:
            f['limit'] = num
        return self.__class__(filters=f)

    def offset(self, num):
        f = dict(self._filters)
        f['offset'] = num
        return self.__class__(filters=f)

    def order_by(self, rule):
        f = dict(self._filters)
        if rule.startswith('-'):
            field_name = rule[1:]
        else:
            field_name = rule
        if self.Entity.allowed_to_sort_by(field_name):
            f['order_by'] = rule
            return self.__class__(filters=f)
        else:
            raise InvalidOrder, (rule,)

    def fetch(self):
        return list(self)

    def __bool__(self):
        return len(self) > 0

    def __nonzero__(self):
        return len(self) > 0

    def __len__(self):
        if self._cached is not None:
            if 'limit' not in self._filters:
                return int(self._cached['meta']['total_count'])
            else:
                return len(self._cached['objects'])
        else:
            lazy_fetch = iter(self)
            try:
                lazy_fetch.next()
            except StopIteration:
                pass
            if 'limit' not in self._filters:
                return int(self._cached['meta']['total_count'])
            else:
                return len(self._cached['objects'])

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
            o = self._make_instance(pre_filled=info)
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
                o = self._make_instance(pre_filled=info)
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

    # TODO: HACK! remove this or rework
    def create(self, **initial):
        o = self._make_instance()
        for pname, value in initial.iteritems():
            setattr(o, pname, value)
        o.save()
        return o

    # WARNING: HACKS below
    # TODO: parent has classmethod, but here we specify object method
    def _resource_point(self):
        c = connection.get_default_connection()
        return c.objects(self.entity_name()).sub(self._lnk_ename, self._main_id)

    # TODO: parent has class method!
    def _make_instance(self, *args, **kwargs):
        return self.Entity(self._lnk_ename, self._main_id, *args, **kwargs)
