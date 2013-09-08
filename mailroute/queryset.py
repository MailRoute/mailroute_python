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


class QueryResource(object):

    COMMANDS = set(['limit', 'offset', 'order_by', 'q'])

    def __init__(self, Entity):
        self.Entity = Entity

    def make_instance(self, *args, **kwargs):
        return self.Entity(*args, **kwargs)

    def new_instance(self, initial, (args, kwargs)):
        o = self.make_instance(*args, **kwargs)
        # because we really want to mark fields to be changed in this case
        for pname, value in initial.iteritems():
            setattr(o, pname, value)
        return o

    def entity_name(self):
        return self.Entity.entity_name()

    def point(self):
        c = connection.get_default_connection()
        return c.objects(self.entity_name())

    def allowed_to_filter_by(self, field_name):
        return field_name in self.COMMANDS or \
            self.Entity.allowed_to_filter_by(field_name)

    def allowed_to_sort_by(self, field_name):
        return self.Entity.allowed_to_sort_by(field_name)

class QuerySet(object):
    '''
    It's a base class for entire collections operations.
    '''

    _virtual = False
    ResourceClass = QueryResource

    @classmethod
    def get(cls, id):
        res = cls.ResourceClass(cls.Entity)
        o = res.make_instance(pre_filled=res.point().one(id).get())
        return o

    @classmethod
    def create(cls, **initial):
        res = cls.ResourceClass(cls.Entity)
        o = res.new_instance(initial, ((), {}))
        o.save()
        return o

    @classmethod
    def bulk_create(cls, descriptions):
        for initial in descriptions:
            cls.create(**initial)

    @classmethod
    def all(cls):
        return FilteredSubSet(cls.ResourceClass(cls.Entity))

    @classmethod
    def filter(cls, **options):
        res = cls.ResourceClass(cls.Entity)
        return FilteredSubSet(res, filters=options)

    @classmethod
    def search(cls, pattern):
        return FilteredSubSet(cls.ResourceClass(cls.Entity), filters=dict(q=pattern))

    @classmethod
    def delete(cls, resources):
        issues = []
        res = cls.ResourceClass(cls.Entity)
        for entity in resources:
            if isinstance(entity, (basestring, int)):
                oid = str(entity)
                try:
                    res.point().one(oid).delete()
                except connection.NotFound, e:
                    issues.append((oid, e))
            else:
                try:
                    entity.delete()
                except Exception, e:
                    issues.append((entity, e))
        if issues:
            raise DeleteError, (issues,)

class FilteredSubSet(object):

    _virtual = False

    def __init__(self, resource, filters={}):
        self._res = resource

        for field_rule in filters:
            field_name = field_rule.split('__')[0]
            if not self._res.allowed_to_filter_by(field_name):
                raise InvalidFilter, field_name

        self._filters = filters
        self._cached = None

    def create(self, **initial):
        o = self._res.new_instance(initial, ((), {}))
        o.save()
        return o

    def filter(self, **options):
        instance_filter = dict(options)
        instance_filter.update(self._filters)
        return self.__class__(self._res, filters=instance_filter)

    def search(self, pattern):
        entire_filter = dict(q=pattern)
        entire_filter.update(self._filters)
        return self.__class__(self._res, filters=entire_filter)

    def all(self):
        return self.__class__(self._res, filters=self._filters)

    def limit(self, num):
        f = dict(self._filters)
        if 'limit' in f:
            f['limit'] = min(f['limit'], num)
        else:
            f['limit'] = num
        return self.__class__(self._res, filters=f)

    def offset(self, num):
        f = dict(self._filters)
        f['offset'] = num
        return self.__class__(self._res, filters=f)

    def order_by(self, rule):
        f = dict(self._filters)
        if rule.startswith('-'):
            field_name = rule[1:]
        else:
            field_name = rule
        if self._res.allowed_to_sort_by(field_name):
            f['order_by'] = rule
            return self.__class__(self._res, filters=f)
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
            self._fill_cache_until(ind)
            info = self._cached['objects'][ind]
            o = self._res.make_instance(pre_filled=info)
            return o

    def _fill_cache_until(self, ind):
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
            res = self._res.point()
            self._cached = ans = res.get(**self._filters)
        else:
            ans = self._cached

        while True:
            for info in ans['objects']:
                o = self._res.make_instance(pre_filled=info)
                yield o

            if not self._cached['meta']['next']:
                break

            next_piece_url = self._cached['meta']['next']
            ans = c.resource(next_piece_url).get()

            self._cached['meta'] = ans['meta']
            self._cached['objects'].extend(ans['objects'])

class VirtualQueryResource(QueryResource):

    def __init__(self, Entity, linked_to):
        super(VirtualQueryResource, self).__init__(Entity)
        self._lnk_ename, self._main_id = linked_to

    def make_instance(self, *args, **kwargs):
        return super(VirtualQueryResource, self). \
            make_instance(self._lnk_ename, self._main_id, *args, **kwargs)

    def point(self):
        return super(VirtualQueryResource, self).point() \
                                                .sub(self._lnk_ename, self._main_id)

class VirtualQuerySet(FilteredSubSet):

    _virtual = True

    def __init__(self, linked_entity_name, main_id, **kwargs):
        res = VirtualQueryResource(self.Entity, (linked_entity_name, main_id))
        super(VirtualQuerySet, self).__init__(res, **kwargs)
